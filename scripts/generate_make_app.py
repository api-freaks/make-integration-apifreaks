#!/usr/bin/env python3
"""
Generate a Make.com custom-app folder tree from an APIFreaks OpenAPI/Swagger spec.

Usage:
    python generate_make_app.py apifreaks-openapi.json ./make-app

It produces one module per operation:
    make-app/
      general.json
      base.imljson
      connections/apifreaks/{metadata.json,api.imljson,parameters.imljson}
      modules/<name>/{metadata.json,api.imljson,expect.imljson,interface.imljson,samples.imljson}

Mapping rules
-------------
  * base URL + X-apiKey header live in base.imljson, so modules never repeat auth.
  * path params + query params + JSON body properties  ->  mappable parameters (expect.imljson)
  * response schema is an array  ->  Search module (typeId 9); otherwise Action (typeId 4)
  * OpenAPI type  ->  Make type (string=text, integer/number=number, boolean=boolean,
                       array=array, object=collection)

Notes
-----
  * Works with OpenAPI 3.x (requestBody/components) and Swagger 2.0 (parameters/definitions).
  * The output is a *first draft*. Review labels, required flags and interface blocks,
    then push with push_to_make.py or the Make Apps SDK VS Code extension.
"""

import json
import os
import re
import sys

BASE_URL = "https://api.apifreaks.com"
AUTH_HEADER = "X-apiKey"          # applied in base.imljson, stripped from every module
CONNECTION = "apifreaks"

TYPE_ACTION = 4
TYPE_SEARCH = 9

OPENAPI_TO_MAKE = {
    "string": "text",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "array": "array",
    "object": "collection",
}


def slug(text):
    parts = [p for p in re.split(r"[^a-zA-Z0-9]+", text or "") if p]
    if not parts:
        return "operation"
    name = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return name[0].lower() + name[1:]


def title(text):
    text = re.sub(r"[_\-/]+", " ", text or "").strip()
    return re.sub(r"\s+", " ", text).title()


def resolve_ref(spec, node):
    """Follow a single $ref if present."""
    if isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"].lstrip("#/").split("/")
        target = spec
        for part in ref:
            target = target.get(part, {})
        return target
    return node


def make_type(schema):
    if not isinstance(schema, dict):
        return "text"
    t = schema.get("type", "string")
    if isinstance(t, list):  # OpenAPI 3.1 e.g. ["string", "null"]
        t = next((x for x in t if x != "null"), "string")
    return OPENAPI_TO_MAKE.get(t, "text")


def param_from_openapi(spec, p):
    p = resolve_ref(spec, p)
    schema = resolve_ref(spec, p.get("schema", {}))
    entry = {
        "name": p.get("name"),
        "label": title(p.get("name")),
        "type": make_type(schema) if schema else make_type(p),
        "required": bool(p.get("required", False)),
    }
    if p.get("description"):
        entry["help"] = p["description"]
    enum = (schema.get("enum") if schema else None) or p.get("enum")
    if enum:
        entry["type"] = "select"
        entry["options"] = [{"label": str(v), "value": v} for v in enum]
    return entry


def body_params(spec, op):
    """Flatten a JSON request body's top-level properties into mappable params."""
    out = []
    rb = op.get("requestBody")
    if rb:
        rb = resolve_ref(spec, rb)
        content = rb.get("content", {})
        media = content.get("application/json") or next(iter(content.values()), {})
        schema = resolve_ref(spec, media.get("schema", {}))
        required = set(schema.get("required", []))
        for name, prop in (schema.get("properties") or {}).items():
            prop = resolve_ref(spec, prop)
            out.append({
                "name": name,
                "label": title(name),
                "type": make_type(prop),
                "required": name in required,
                **({"help": prop["description"]} if prop.get("description") else {}),
            })
    # Swagger 2.0 body parameter
    for p in op.get("parameters", []):
        p = resolve_ref(spec, p)
        if p.get("in") == "body":
            schema = resolve_ref(spec, p.get("schema", {}))
            required = set(schema.get("required", []))
            for name, prop in (schema.get("properties") or {}).items():
                prop = resolve_ref(spec, prop)
                out.append({
                    "name": name,
                    "label": title(name),
                    "type": make_type(prop),
                    "required": name in required,
                })
    return out


def response_is_array(spec, op):
    responses = op.get("responses", {})
    ok = responses.get("200") or responses.get("201") or next(iter(responses.values()), {})
    ok = resolve_ref(spec, ok)
    schema = ok.get("schema")
    if schema is None:
        content = ok.get("content", {})
        media = content.get("application/json") or next(iter(content.values()), {})
        schema = media.get("schema", {})
    schema = resolve_ref(spec, schema)
    return isinstance(schema, dict) and schema.get("type") == "array"


def build_communication(path, method, path_params, query_params, body_names):
    api = {"url": path, "method": method.upper()}
    for pp in path_params:
        api["url"] = api["url"].replace("{%s}" % pp, "{{parameters.%s}}" % pp)
    if query_params:
        api["qs"] = {q: "{{parameters.%s}}" % q for q in query_params}
    if body_names and method.upper() in ("POST", "PUT", "PATCH"):
        api["body"] = {b: "{{parameters.%s}}" % b for b in body_names}
    api["response"] = {"output": "{{body}}"}
    return api


def write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    spec_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "make-app"

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    os.makedirs(os.path.join(out_dir, "connections", CONNECTION), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "modules"), exist_ok=True)

    # ---- shared components ----
    write(os.path.join(out_dir, "general.json"), {
        "name": CONNECTION, "label": "APIFreaks", "version": 1,
        "theme": "#ffde00", "language": "en", "countries": [],
        "description": (spec.get("info", {}) or {}).get("description",
                       "APIFreaks API hub."),
    })
    write(os.path.join(out_dir, "base.imljson"), {
        "baseUrl": BASE_URL,
        "headers": {AUTH_HEADER: "{{connection.apiKey}}"},
        "response": {"error": {"message": "[{{statusCode}}] {{ifempty(body.message, ifempty(body.error, body))}}"}},
        "log": {"sanitize": ["request.headers.%s" % AUTH_HEADER]},
    })
    conn = os.path.join(out_dir, "connections", CONNECTION)
    write(os.path.join(conn, "metadata.json"),
          {"name": CONNECTION, "label": "APIFreaks connection", "type": "apikey"})
    write(os.path.join(conn, "api.imljson"), {
        "url": BASE_URL + "/v1.0/geolocation/lookup", "method": "GET",
        "qs": {"ip": "8.8.8.8"},
        "headers": {AUTH_HEADER: "{{parameters.apiKey}}"},
        "response": {"error": {"message": "[{{statusCode}}] Invalid API key"}},
        "log": {"sanitize": ["request.headers.%s" % AUTH_HEADER]},
    })
    write(os.path.join(conn, "parameters.imljson"),
          [{"name": "apiKey", "type": "text", "label": "API Key", "required": True}])

    # ---- one module per operation ----
    count = 0
    seen = set()
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            op = op or {}
            name = slug(op.get("operationId") or (method + " " + path))
            orig = name
            i = 2
            while name in seen:
                name = "%s%d" % (orig, i)
                i += 1
            seen.add(name)

            params = [resolve_ref(spec, p) for p in op.get("parameters", [])]
            path_params = [p["name"] for p in params if p.get("in") == "path"]
            query_params = [p["name"] for p in params if p.get("in") == "query"]
            header_params = [p for p in params
                             if p.get("in") == "header" and p.get("name") != AUTH_HEADER]

            expect = []
            for p in params:
                if p.get("in") in ("path", "query"):
                    expect.append(param_from_openapi(spec, p))
                elif p.get("in") == "header" and p.get("name") != AUTH_HEADER:
                    expect.append(param_from_openapi(spec, p))
            body = body_params(spec, op)
            expect.extend(body)

            is_search = response_is_array(spec, op)
            mod_dir = os.path.join(out_dir, "modules", name)
            os.makedirs(mod_dir, exist_ok=True)

            tag = (op.get("tags") or [""])[0]
            summary = op.get("summary") or title(name)
            if len(summary) > 60:
                summary = summary[:60].rsplit(" ", 1)[0] + "..."
            label = ("%s: %s" % (tag, summary)) if tag else summary
            write(os.path.join(mod_dir, "metadata.json"), {
                "name": name,
                "label": label,
                "description": op.get("description") or summary,
                "connection": CONNECTION,
                "typeId": TYPE_SEARCH if is_search else TYPE_ACTION,
            })
            write(os.path.join(mod_dir, "api.imljson"),
                  build_communication(path, method, path_params, query_params,
                                      [b["name"] for b in body]))
            write(os.path.join(mod_dir, "expect.imljson"), expect)
            write(os.path.join(mod_dir, "interface.imljson"), [])   # fill from real responses
            write(os.path.join(mod_dir, "samples.imljson"), {})
            count += 1

    print("Generated %d modules into %s/modules/" % (count, out_dir))


if __name__ == "__main__":
    main()
