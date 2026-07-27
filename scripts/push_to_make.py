#!/usr/bin/env python3
"""
Synchronize a generated make-app/ folder with an EXISTING Make custom app.

Default behavior is update-only:
  * Reuses the existing SDK app.
  * Reuses an existing connection component.
  * Updates Base, connection sections, existing module metadata/sections, and Groups.
  * NEVER creates a missing connection or module unless --create-missing is supplied.

Prerequisites
-------------
  * A paid Make plan.
  * An API token with SDK app read/write scopes.
  * Environment variables:
        export MAKE_TOKEN="..."
        export MAKE_ZONE="https://eu1.make.com"

Safe usage
----------
    python3 push_to_make.py ./make-app --limit 1 --verbose
    python3 push_to_make.py ./make-app --verbose

To permit genuinely new modules/connections:
    python3 push_to_make.py ./make-app --create-missing --verbose

When an app has duplicate connection components, specify the correct one:
    python3 push_to_make.py ./make-app \
        --connection-name apifreaks-xxxxxxxx --verbose
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Iterable, Optional

TOKEN = os.environ.get("MAKE_TOKEN")
ZONE = os.environ.get("MAKE_ZONE", "https://eu1.make.com").rstrip("/")
API = ZONE + "/api/v2"

# Make is behind Cloudflare, which may reject urllib's default user-agent.
UA = os.environ.get(
    "MAKE_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36",
)

VERBOSE = False


def req(method: str, url: str, body: Any = None, ctype: str = "application/json"):
    if body is None:
        data = None
    elif isinstance(body, (dict, list)):
        data = json.dumps(body).encode("utf-8")
    else:
        data = str(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", "Token " + (TOKEN or ""))
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", UA)
    if data is not None:
        request.add_header("Content-Type", ctype)

    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = raw
            return response.status, parsed
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        return error.code, parsed
    except urllib.error.URLError as error:
        return 0, {"message": str(error.reason), "code": "NETWORK_ERROR"}


def load(path: str):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def first_dict_value(obj: Any, *keys: str):
    if not isinstance(obj, dict):
        return None
    for key in keys:
        if key in obj:
            return obj[key]
    return None


def find_list(obj: Any, preferred_keys: Iterable[str]) -> Optional[list]:
    """Find the most likely resource list in a Make API response."""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return None

    for key in preferred_keys:
        value = obj.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = find_list(value, preferred_keys)
            if nested is not None:
                return nested

    # Pagination wrappers vary between Make API releases/zones.
    for key in ("data", "result", "response"):
        value = obj.get(key)
        if isinstance(value, (dict, list)):
            nested = find_list(value, preferred_keys)
            if nested is not None:
                return nested

    return None


def put_first(candidates: list[str], payload: Any, ctype: str = "application/jsonc"):
    """Try PUT URL variants until one succeeds. Return status, URL, response."""
    last_status, last_body, last_url = 0, None, ""
    for url in candidates:
        status, body = req("PUT", url, payload, ctype=ctype)
        if VERBOSE:
            print("      PUT", url, "->", status)
        last_status, last_body, last_url = status, body, url
        if status < 400:
            return status, url, body
    return last_status, last_url, last_body


# ---------- app ----------
def list_apps() -> list[dict]:
    for query in (
        "?cols=name,label,version&pg[limit]=1000",
        "?pg[limit]=1000",
        "",
    ):
        status, response = req("GET", API + "/sdk/apps" + query)
        if status < 400:
            apps = find_list(response, ("apps", "sdkApps", "items"))
            if isinstance(apps, list):
                return [item for item in apps if isinstance(item, dict)]
    return []


def ensure_app(general: dict, create_missing: bool):
    name_hint = general["name"]
    label = general["label"]

    for app in list_apps():
        if app.get("label") == label or str(app.get("name", "")).startswith(name_hint):
            name = app.get("name")
            version = app.get("version", general.get("version", 1))
            print("reusing existing app:", name, "v", version)
            return name, version

    if not create_missing:
        sys.exit(
            "Existing Make app not found. Nothing was created. "
            "Use --create-missing only if you intentionally want a new app."
        )

    status, response = req("POST", API + "/sdk/apps", general)
    print("create app:", status)
    if status >= 400:
        sys.exit("Could not create app: %s" % response)

    app = first_dict_value(response, "app", "sdkApp") or response
    name = app.get("name") if isinstance(app, dict) else None
    version = (
        app.get("version") if isinstance(app, dict) else None
    ) or general.get("version", 1)

    if not name:
        sys.exit("App was created, but its generated Make name could not be determined.")
    return name, version


def update_base(app: str, version: int, app_dir: str) -> bool:
    path = os.path.join(app_dir, "base.imljson")
    if not os.path.exists(path):
        print("set base: skipped (base.imljson not found)")
        return True

    status, _, body = put_first(
        [
            f"{API}/sdk/apps/{app}/{version}/base",
            f"{API}/sdk/apps/{app}/base",
        ],
        load(path),
    )
    print("set base:", status)
    if status >= 400:
        print("   ", body)
        return False
    return True


# ---------- modules ----------
def list_modules(app: str, version: int) -> list[dict]:
    candidates = [
        f"{API}/sdk/apps/{app}/{version}/modules?pg[limit]=1000",
        f"{API}/sdk/apps/{app}/{version}/modules",
    ]
    last_error = None

    for url in candidates:
        status, response = req("GET", url)
        if VERBOSE:
            print("      GET", url, "->", status)
        if status < 400:
            modules = find_list(
                response,
                ("modules", "sdkModules", "appModules", "items"),
            )
            if isinstance(modules, list):
                return [item for item in modules if isinstance(item, dict)]
            last_error = "Successful response did not contain a module list: %r" % response
        else:
            last_error = response

    sys.exit(
        "Could not list existing modules safely. The script stopped before creating "
        "or modifying module components. Last response: %s" % last_error
    )


def module_name(module: dict) -> Optional[str]:
    return (
        module.get("name")
        or module.get("moduleName")
        or module.get("id")
    )


def connection_references_from_modules(modules: list[dict]) -> list[str]:
    references = []
    for module in modules:
        for key in ("connection", "connectionName", "appConnection"):
            value = module.get(key)
            if isinstance(value, str) and value and value not in references:
                references.append(value)
            elif isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str) and name and name not in references:
                    references.append(name)
    return references


def create_module(app: str, version: int, meta: dict, connection_name: Optional[str]):
    payload = {
        "name": meta["name"],
        "label": meta["label"],
        "description": meta.get("description", ""),
        "typeId": meta["typeId"],
        "connection": connection_name or meta.get("connection"),
    }
    return req("POST", f"{API}/sdk/apps/{app}/{version}/modules", payload)


def update_module_metadata(
    app: str,
    version: int,
    meta: dict,
    connection_name: Optional[str],
):
    """
    Update mutable module metadata when the Make zone supports this endpoint.

    Section updates are still authoritative. A 404/405 here is treated as a
    non-fatal compatibility condition because older zones expose section PUTs
    but not module-metadata PUT through the same path.
    """
    name = meta["name"]
    payload = {
        "label": meta["label"],
        "description": meta.get("description", ""),
        "typeId": meta["typeId"],
        "connection": connection_name or meta.get("connection"),
    }
    return put_first(
        [
            f"{API}/sdk/apps/{app}/{version}/modules/{name}",
            f"{API}/sdk/apps/modules/{name}",
        ],
        payload,
        ctype="application/json",
    )


def upload_module_sections(app: str, version: int, name: str, module_dir: str) -> bool:
    success = True
    found_section = False

    for section, filename in (
        ("api", "api.imljson"),
        ("expect", "expect.imljson"),
        ("interface", "interface.imljson"),
        ("samples", "samples.imljson"),
    ):
        path = os.path.join(module_dir, filename)
        if not os.path.exists(path):
            continue

        found_section = True
        status, _, body = put_first(
            [
                f"{API}/sdk/apps/{app}/{version}/modules/{name}/{section}",
                f"{API}/sdk/apps/modules/{name}/{section}",
            ],
            load(path),
        )

        if status >= 400:
            success = False
            print(f"      {section}: {status} {body}")
        elif VERBOSE:
            print(f"      {section}: {status}")

    if not found_section:
        print("      warning: no module section files found")
    return success


# ---------- connection ----------
def list_connections(app: str) -> list[dict]:
    candidates = [
        f"{API}/sdk/apps/{app}/connections?pg[limit]=1000",
        f"{API}/sdk/apps/{app}/connections",
    ]
    for url in candidates:
        status, response = req("GET", url)
        if VERBOSE:
            print("      GET", url, "->", status)
        if status < 400:
            connections = find_list(
                response,
                ("appConnections", "connections", "sdkConnections", "items"),
            )
            if isinstance(connections, list):
                return [item for item in connections if isinstance(item, dict)]
    return []


def connection_name(connection: dict) -> Optional[str]:
    return connection.get("name") or connection.get("connectionName")


def create_connection(app: str, meta: dict):
    payload = {
        "type": meta.get("type", "apikey"),
        "label": meta.get("label", "Connection"),
    }
    return req("POST", f"{API}/sdk/apps/{app}/connections", payload)


def choose_connection(
    app: str,
    local_folder_name: str,
    meta: dict,
    module_connection_references: list[str],
    requested_name: Optional[str],
    create_missing: bool,
) -> str:
    connections = list_connections(app)
    by_name = {
        connection_name(item): item
        for item in connections
        if connection_name(item)
    }

    if requested_name:
        if requested_name in by_name:
            print("reusing requested connection:", requested_name)
            return requested_name
        available = ", ".join(sorted(by_name)) or "none"
        sys.exit(
            f"Connection {requested_name!r} was not found. Available: {available}"
        )

    # Best choice: the connection currently referenced by existing modules.
    for reference in module_connection_references:
        if reference in by_name:
            print("reusing module-referenced connection:", reference)
            return reference

    label = meta.get("label", "Connection")
    type_name = meta.get("type", "apikey")

    exact_matches = [
        item
        for item in connections
        if item.get("label") == label
        and (not item.get("type") or item.get("type") == type_name)
    ]
    if exact_matches:
        selected = connection_name(exact_matches[0])
        if len(exact_matches) > 1:
            names = ", ".join(
                connection_name(item) or "<unknown>" for item in exact_matches
            )
            print(
                "warning: multiple matching connections found:",
                names,
            )
            print(
                "         selected:",
                selected,
                "(use --connection-name to override)",
            )
        else:
            print("reusing existing connection:", selected)
        return selected

    folder_matches = [
        item
        for item in connections
        if (connection_name(item) or "") == local_folder_name
        or (connection_name(item) or "").startswith(local_folder_name + "-")
    ]
    if folder_matches:
        selected = connection_name(folder_matches[0])
        print("reusing folder-matched connection:", selected)
        return selected

    if len(connections) == 1:
        selected = connection_name(connections[0])
        print("reusing only available connection:", selected)
        return selected

    if not create_missing:
        available = ", ".join(sorted(by_name)) or "none"
        sys.exit(
            "No unambiguous existing connection could be selected. "
            f"Available connections: {available}. Pass --connection-name NAME. "
            "Nothing new was created."
        )

    status, response = create_connection(app, meta)
    print("create connection:", status)
    if status >= 400:
        sys.exit("Could not create connection: %s" % response)

    connection = first_dict_value(response, "appConnection", "connection") or response
    generated_name = connection_name(connection) if isinstance(connection, dict) else None
    if not generated_name:
        sys.exit("Connection was created, but its generated name could not be determined.")
    return generated_name


def update_connection_metadata(app: str, name: str, meta: dict):
    payload = {
        "type": meta.get("type", "apikey"),
        "label": meta.get("label", "Connection"),
    }
    return put_first(
        [
            f"{API}/sdk/apps/{app}/connections/{name}",
            f"{API}/sdk/apps/connections/{name}",
        ],
        payload,
        ctype="application/json",
    )


def upload_connection_sections(app: str, name: str, connection_dir: str) -> bool:
    success = True
    for section, filename in (
        ("api", "api.imljson"),
        ("parameters", "parameters.imljson"),
    ):
        path = os.path.join(connection_dir, filename)
        if not os.path.exists(path):
            continue

        status, _, body = put_first(
            [
                f"{API}/sdk/apps/{app}/connections/{name}/{section}",
                f"{API}/sdk/apps/connections/{name}/{section}",
            ],
            load(path),
        )
        print(f"   connection {section}:", status)
        if status >= 400:
            success = False
            print("      ", body)
    return success


# ---------- groups ----------
def update_groups(app: str, version: int, app_dir: str) -> bool:
    path = os.path.join(app_dir, "groups.json")
    if not os.path.exists(path):
        print("set groups: skipped (groups.json not found)")
        return True

    status, _, body = put_first(
        [
            f"{API}/sdk/apps/{app}/{version}/groups",
            f"{API}/sdk/apps/{app}/groups",
        ],
        load(path),
    )
    print("set groups:", status)
    if status >= 400:
        print("   ", body)
        return False
    return True


def main():
    global VERBOSE

    parser = argparse.ArgumentParser()
    parser.add_argument("app_dir")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="update at most N modules (0 = all)",
    )
    parser.add_argument("--sleep", type=float, default=0.3)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="allow creation of a missing app, connection, or module",
    )
    parser.add_argument(
        "--connection-name",
        default=os.environ.get("MAKE_CONNECTION_NAME"),
        help="exact generated Make connection component name to reuse",
    )
    args = parser.parse_args()
    VERBOSE = args.verbose

    if not TOKEN:
        sys.exit("Set MAKE_TOKEN (and MAKE_ZONE) first.")

    app_dir = args.app_dir.rstrip("/")
    general_path = os.path.join(app_dir, "general.json")
    if not os.path.exists(general_path):
        sys.exit("general.json not found under: " + app_dir)

    general = load(general_path)
    app, version = ensure_app(general, create_missing=args.create_missing)
    print("=> using app:", app, "version", version)
    print(
        "=> mode:",
        "create-or-update" if args.create_missing else "UPDATE EXISTING ONLY",
    )

    overall_failed = not update_base(app, version, app_dir)

    existing_modules = list_modules(app, version)
    existing_by_name = {
        module_name(item): item
        for item in existing_modules
        if module_name(item)
    }
    print("=> existing modules found:", len(existing_by_name))

    module_connection_references = connection_references_from_modules(existing_modules)

    selected_connection = None
    connection_root = os.path.join(app_dir, "connections")
    if os.path.isdir(connection_root):
        connection_folders = sorted(
            name
            for name in os.listdir(connection_root)
            if os.path.isdir(os.path.join(connection_root, name))
        )

        if len(connection_folders) > 1:
            print(
                "warning: multiple local connection folders found; "
                "modules will use the last processed connection."
            )

        for local_name in connection_folders:
            connection_dir = os.path.join(connection_root, local_name)
            metadata_path = os.path.join(connection_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                print("skipping connection without metadata.json:", local_name)
                continue

            metadata = load(metadata_path)
            selected_connection = choose_connection(
                app=app,
                local_folder_name=local_name,
                meta=metadata,
                module_connection_references=module_connection_references,
                requested_name=args.connection_name,
                create_missing=args.create_missing,
            )
            print("=> connection name:", selected_connection)

            metadata_status, _, metadata_body = update_connection_metadata(
                app, selected_connection, metadata
            )
            if metadata_status >= 400 and VERBOSE:
                print(
                    "   connection metadata update not supported/failed:",
                    metadata_status,
                    metadata_body,
                )

            if not upload_connection_sections(
                app, selected_connection, connection_dir
            ):
                overall_failed = True
            time.sleep(args.sleep)

    module_root = os.path.join(app_dir, "modules")
    if not os.path.isdir(module_root):
        sys.exit("modules directory not found under: " + app_dir)

    local_module_folders = sorted(
        name
        for name in os.listdir(module_root)
        if os.path.isdir(os.path.join(module_root, name))
    )
    if args.limit:
        local_module_folders = local_module_folders[: args.limit]

    updated = created = skipped = failed = 0

    for index, folder_name in enumerate(local_module_folders, 1):
        module_dir = os.path.join(module_root, folder_name)
        metadata_path = os.path.join(module_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            skipped += 1
            print(
                "[%d/%d] %s: skipped (metadata.json missing)"
                % (index, len(local_module_folders), folder_name)
            )
            continue

        metadata = load(metadata_path)
        name = metadata["name"]
        exists = name in existing_by_name

        if not exists and not args.create_missing:
            skipped += 1
            print(
                "[%d/%d] %s: skipped (not present in Make; update-only mode)"
                % (index, len(local_module_folders), name)
            )
            continue

        if not exists:
            status, response = create_module(
                app,
                version,
                metadata,
                selected_connection or metadata.get("connection"),
            )
            if status >= 400:
                failed += 1
                overall_failed = True
                print(
                    "[%d/%d] %s: create failed: %s %s"
                    % (index, len(local_module_folders), name, status, response)
                )
                time.sleep(args.sleep)
                continue
            created += 1
            existing_by_name[name] = {"name": name}
        else:
            metadata_status, _, metadata_body = update_module_metadata(
                app,
                version,
                metadata,
                selected_connection or metadata.get("connection"),
            )
            if metadata_status >= 400 and VERBOSE:
                print(
                    "      metadata update not supported/failed:",
                    metadata_status,
                    metadata_body,
                )

        sections_ok = upload_module_sections(app, version, name, module_dir)
        if sections_ok:
            if exists:
                updated += 1
                action = "updated"
            else:
                action = "created"
            print(
                "[%d/%d] %s: %s"
                % (index, len(local_module_folders), name, action)
            )
        else:
            failed += 1
            overall_failed = True
            print(
                "[%d/%d] %s: section update failed"
                % (index, len(local_module_folders), name)
            )

        time.sleep(args.sleep)

    # Keep the old behavior: when --limit is used, do not update all groups because
    # groups may reference modules intentionally excluded from the test run.
    if not args.limit:
        if not update_groups(app, version, app_dir):
            overall_failed = True
    else:
        print("set groups: skipped because --limit was used")

    print("\ndone.")
    print("modules updated:", updated)
    print("modules created:", created)
    print("modules skipped:", skipped)
    print("modules failed:", failed)

    if overall_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()