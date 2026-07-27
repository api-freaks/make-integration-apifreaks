#!/usr/bin/env python3
"""
Push a generated make-app/ folder to Make.com via the SDK Apps REST API.

Key fix over v1: Make appends a unique suffix to SDK app (and connection) names,
so we never assume the name is "apifreaks". We create-or-reuse the app, then read
the REAL name/version/connection-name back from Make and use those everywhere.
Section upload URLs are tried against the known Make path shapes until one works,
so small differences between Make zones/versions don't stop the run.

Prereqs
-------
  * PAID Make plan; API token (profile -> API -> Add token) with SDK app scopes.
  * export MAKE_TOKEN="..."   and   export MAKE_ZONE="https://eu1.make.com"  (your zone)

Usage
-----
    python3 push_to_make.py ./make-app --limit 1     # test ONE module first
    python3 push_to_make.py ./make-app               # full run
    python3 push_to_make.py ./make-app --verbose     # print URLs tried
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("MAKE_TOKEN")
ZONE = os.environ.get("MAKE_ZONE", "https://eu1.make.com").rstrip("/")
API = ZONE + "/api/v2"

# Make is behind Cloudflare, which bans the default Python-urllib user-agent (error 1010).
UA = os.environ.get("MAKE_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

VERBOSE = False


def req(method, url, body=None, ctype="application/json"):
    if body is None:
        data = None
    elif isinstance(body, (dict, list)):
        data = json.dumps(body).encode()
    else:
        data = str(body).encode()
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", "Token " + (TOKEN or ""))
    r.add_header("Accept", "application/json")
    r.add_header("User-Agent", UA)
    if data is not None:
        r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dig(obj, *keys):
    """Return first present key from a dict, else the object itself if it's a list."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                return obj[k]
    return None


def put_first(candidates, payload):
    """Try each URL until one returns <400. Returns (status, url, body)."""
    st, body, url = 0, None, ""
    for url in candidates:
        st, body = req("PUT", url, payload, ctype="application/jsonc")
        if VERBOSE:
            print("      PUT", url, "->", st)
        if st < 400:
            return st, url, body
    return st, url, body


# ---------- app ----------
def list_apps():
    for q in ("?cols=name,label,version&pg[limit]=1000", "?pg[limit]=1000", ""):
        st, resp = req("GET", API + "/sdk/apps" + q)
        if st < 400:
            apps = dig(resp, "apps", "sdkApps")
            if isinstance(apps, list):
                return apps
    return []


def ensure_app(general):
    name_hint, label = general["name"], general["label"]
    for a in list_apps():
        if a.get("label") == label or str(a.get("name", "")).startswith(name_hint):
            print("reusing existing app:", a["name"], "v", a.get("version", 1))
            return a["name"], a.get("version", general.get("version", 1))
    st, resp = req("POST", API + "/sdk/apps", general)
    print("create app:", st)
    if st >= 400:
        print("   ", resp)
    app = dig(resp, "app", "sdkApp") or resp
    name = app.get("name") if isinstance(app, dict) else None
    ver = (app.get("version") if isinstance(app, dict) else None) or general.get("version", 1)
    if not name:
        for a in list_apps():
            if a.get("label") == label or str(a.get("name", "")).startswith(name_hint):
                name, ver = a["name"], a.get("version", 1)
                break
    return name, ver


# ---------- connection ----------
def ensure_connection(app, cmeta):
    st, resp = req("POST", "%s/sdk/apps/%s/connections" % (API, app),
                   {"type": cmeta.get("type", "apikey"), "label": cmeta.get("label", "Connection")})
    print("create connection:", st)
    if st >= 400:
        print("   ", resp)
    conn = dig(resp, "appConnection", "connection") or resp
    name = conn.get("name") if isinstance(conn, dict) else None
    if not name:
        st2, r2 = req("GET", "%s/sdk/apps/%s/connections" % (API, app))
        lst = dig(r2, "appConnections", "connections")
        if isinstance(lst, list) and lst:
            name = lst[-1].get("name")
    return name


def upload_connection_sections(app, cname, cdir):
    for section, fname in (("api", "api.imljson"), ("parameters", "parameters.imljson")):
        fp = os.path.join(cdir, fname)
        if not os.path.exists(fp):
            continue
        payload = load(fp)
        st, url, _ = put_first([
            "%s/sdk/apps/%s/connections/%s/%s" % (API, app, cname, section),
            "%s/sdk/apps/connections/%s/%s" % (API, cname, section),
        ], payload)
        print("   connection %s:" % section, st)


# ---------- modules ----------
def create_module(app, ver, meta, conn_name):
    return req("POST", "%s/sdk/apps/%s/%s/modules" % (API, app, ver), {
        "name": meta["name"],
        "label": meta["label"],
        "description": meta.get("description", ""),
        "typeId": meta["typeId"],
        "connection": conn_name,
    })


def upload_module_sections(app, ver, mname, mdir):
    for section, fname in (("api", "api.imljson"), ("expect", "expect.imljson"),
                           ("interface", "interface.imljson"), ("samples", "samples.imljson")):
        fp = os.path.join(mdir, fname)
        if not os.path.exists(fp):
            continue
        payload = load(fp)
        put_first([
            "%s/sdk/apps/%s/%s/modules/%s/%s" % (API, app, ver, mname, section),
            "%s/sdk/apps/modules/%s/%s" % (API, mname, section),
        ], payload)


def main():
    global VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("app_dir")
    ap.add_argument("--limit", type=int, default=0, help="push at most N modules (0 = all)")
    ap.add_argument("--sleep", type=float, default=0.3)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    VERBOSE = args.verbose

    if not TOKEN:
        sys.exit("Set MAKE_TOKEN (and MAKE_ZONE) first.")

    d = args.app_dir.rstrip("/")
    general = load(os.path.join(d, "general.json"))

    app, ver = ensure_app(general)
    if not app:
        sys.exit("Could not determine the created app name. Check token scopes / zone.")
    print("=> using app:", app, "version", ver)

    base = load(os.path.join(d, "base.imljson"))
    st, url, _ = put_first([
        "%s/sdk/apps/%s/%s/base" % (API, app, ver),
        "%s/sdk/apps/%s/base" % (API, app),
    ], base)
    print("set base:", st)

    conn_name = None
    cdir_root = os.path.join(d, "connections")
    if os.path.isdir(cdir_root):
        for cname in os.listdir(cdir_root):
            cpath = os.path.join(cdir_root, cname)
            meta = load(os.path.join(cpath, "metadata.json"))
            conn_name = ensure_connection(app, meta)
            print("=> connection name:", conn_name)
            if conn_name:
                upload_connection_sections(app, conn_name, cpath)
            time.sleep(args.sleep)

    mroot = os.path.join(d, "modules")
    names = sorted(os.listdir(mroot))
    if args.limit:
        names = names[:args.limit]
    ok = fail = 0
    for i, mname in enumerate(names, 1):
        mdir = os.path.join(mroot, mname)
        meta = load(os.path.join(mdir, "metadata.json"))
        st, resp = create_module(app, ver, meta, conn_name or meta.get("connection"))
        if st < 400:
            ok += 1
            upload_module_sections(app, ver, meta["name"], mdir)
            print("[%d/%d] %s: %s" % (i, len(names), mname, st))
        else:
            fail += 1
            print("[%d/%d] %s: %s %s" % (i, len(names), mname, st, resp))
        time.sleep(args.sleep)

    # ---- groups (uploaded after modules, since they reference module names) ----
    gpath = os.path.join(d, "groups.json")
    if os.path.exists(gpath) and not args.limit:
        groups = load(gpath)
        st, url, _ = put_first([
            "%s/sdk/apps/%s/%s/groups" % (API, app, ver),
            "%s/sdk/apps/%s/groups" % (API, app),
        ], groups)
        print("set groups:", st)

    print("\ndone. modules created: %d, failed: %d" % (ok, fail))


if __name__ == "__main__":
    main()