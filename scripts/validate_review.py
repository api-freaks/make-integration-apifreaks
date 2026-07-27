#!/usr/bin/env python3
"""Check the generated Make app against every item in the Make.com review.

Usage: python3 scripts/validate_review.py [make-app]

Exits non-zero if any item regresses, so it can gate a re-submission.
"""
import json
import os
import re
import sys

APP = sys.argv[1] if len(sys.argv) > 1 else "make-app"
MODS = os.path.join(APP, "modules")

fail = []
info = []


def check(ok, item, detail=""):
    (info if ok else fail).append("%s %s%s" % ("PASS" if ok else "FAIL", item,
                                               (" - " + detail) if detail else ""))


def load(mod, fn):
    p = os.path.join(MODS, mod, fn)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


mods = sorted(os.listdir(MODS))

# --- everything parses -------------------------------------------------------
bad = []
for m in mods:
    for fn in ("metadata.json", "api.imljson", "expect.imljson",
               "interface.imljson", "samples.imljson"):
        try:
            load(m, fn)
        except Exception as e:
            bad.append("%s/%s: %s" % (m, fn, e))
check(not bad, "all module files are valid JSON", "; ".join(bad[:5]))

# --- technical blockers ------------------------------------------------------
ua = load("getUserAgentLookup", "api.imljson")
check(ua.get("headers", {}).get("User-Agent", "").startswith("{{parameters."),
      "getUserAgentLookup sends the User-Agent header")

up = load("postPdfResourceUploadBinary", "api.imljson")
upe = load("postPdfResourceUploadBinary", "expect.imljson")
check(bool(up.get("body")) and any(p.get("semantic") == "file:data" for p in upe),
      "postPdfResourceUploadBinary uploads a file buffer as the body")

mac = load("makeApiCall", "expect.imljson")
url = next((p for p in mac if p["name"] == "url"), {})
check("elative" in url.get("help", ""),
      "makeApiCall url is documented as a relative path")
maci = load("makeApiCall", "interface.imljson")
check({"statusCode", "headers", "body"} <= {f["name"] for f in maci},
      "makeApiCall returns statusCode, headers and body")
hdr = next((p for p in mac if p["name"] == "headers"), {})
check("onnection" in hdr.get("help", ""),
      "makeApiCall Headers help notes auth is already handled")

for m in mods:
    names = [p["name"] for p in load(m, "expect.imljson")]
    if len(names) != len(set(names)):
        dup = sorted({n for n in names if names.count(n) > 1})
        check(False, "%s has duplicate parameters" % m, ",".join(dup))
check(True, "no module defines a parameter twice")

# --- logical blockers --------------------------------------------------------
empty = [m for m in mods if not load(m, "interface.imljson")]
check(not empty, "every module defines an output interface",
      "%d empty: %s" % (len(empty), ",".join(empty[:5])))

run_together = re.compile(r"[a-z][A-Z]")
rt = set()


def walk(spec):
    for f in spec:
        if run_together.search(f.get("label", "")):
            rt.add(f["label"])
        if isinstance(f.get("spec"), list):
            walk(f["spec"])


for m in mods:
    walk(load(m, "interface.imljson"))
    walk(load(m, "expect.imljson"))
check(not rt, "no run-together labels (CountryCode / ASNumber / WHOISServer)",
      ",".join(sorted(rt)[:5]))

REVIEWER_SEARCH = [
    "bulkIpLookup", "bulkIpLookupV2", "bulkIpSecurityLookup", "getFlagsSupported",
    "getGeocoderSearch", "getSwiftCodeFinder", "getVatRatesCountry",
    "getVatRatesIpAddress", "postPhoneValidationBulk", "postUserAgentLookup",
]
for m in REVIEWER_SEARCH:
    md, api, exp = load(m, "metadata.json"), load(m, "api.imljson"), load(m, "expect.imljson")
    r = api.get("response", {})
    out = r.get("output")
    out_ok = out == "{{item}}" or (isinstance(out, dict) and "{{item}}" in json.dumps(out))
    ok = (md.get("typeId") == 9 and r.get("iterate") and out_ok
          and r.get("limit") and any(p["name"] == "limit" for p in exp))
    check(ok, "%s is a search module with iterate/item/limit" % m)

PAGINATED = ["dnsHistoryLookup", "getDomainWhoisReverse", "getSubdomainsLookup",
             "reverseDnsLookup", "searchZipByCity", "searchZipByRadius",
             "searchZipByRegion"]
for m in PAGINATED:
    api, exp = load(m, "api.imljson"), load(m, "expect.imljson")
    check("pagination" in api and not any(p["name"] == "page" for p in exp),
          "%s paginates instead of exposing a raw page input" % m)

xml = [m for m in mods if '"xml"' in json.dumps(load(m, "expect.imljson"))]
check(not xml, "no module offers an xml response format", ",".join(xml))

READABILITY = ["grammarCorrect", "grammarDetect", "readabilityScore", "weakWordsDetect"]
for m in READABILITY:
    names = {p["name"].lower() for p in load(m, "expect.imljson")}
    check("apikey" not in names, "%s does not re-ask for the API key" % m)

# every declared parameter is actually referenced by the request
for m in mods:
    if m == "makeApiCall":
        continue
    api = json.dumps(load(m, "api.imljson"))
    unused = [p["name"] for p in load(m, "expect.imljson")
              if p["name"] not in ("limit",) and "parameters.%s" % p["name"] not in api]
    if unused:
        check(False, "%s collects inputs it never sends" % m, ",".join(unused))
check(True, "no module collects an input it never sends")

for m, hdr in (("getGeocoderReverse", "Accept-Language"),
               ("getGeocoderSearch", "Accept-Language")):
    check(hdr in load(m, "api.imljson").get("headers", {}),
          "%s wires the %s header" % (m, hdr))
wh = [m for m in mods
      if any(p["name"] == "XWebhookAuthorization" for p in load(m, "expect.imljson"))]
for m in wh:
    check("X-Webhook-Authorization" in load(m, "api.imljson").get("headers", {}),
          "%s wires the X-Webhook-Authorization header" % m)

for m in ("getPdfResourceDownload", "websiteScreenshot"):
    api, iface = load(m, "api.imljson"), load(m, "interface.imljson")
    check(api.get("response", {}).get("type") == "binary"
          and any(f.get("semantic") == "file:data" for f in iface),
          "%s returns a binary buffer" % m)

textfile = []
for m in mods:
    for p in load(m, "expect.imljson"):
        if p.get("semantic") == "file:data" and p["type"] != "buffer":
            textfile.append("%s.%s" % (m, p["name"]))
check(not textfile, "every file upload input is a buffer", ",".join(textfile))

# --- connection --------------------------------------------------------------
cp = json.load(open(os.path.join(APP, "connections/apifreaks/parameters.imljson")))
check(all(p["type"] == "password" for p in cp if "key" in p["name"].lower()),
      "connection API key is a password field")
ca = json.load(open(os.path.join(APP, "connections/apifreaks/api.imljson")))
check("credits/usage/info" in ca["url"],
      "connection test uses the free credits endpoint")

# --- grouping / naming -------------------------------------------------------
groups = json.load(open(os.path.join(APP, "groups.json")))
grouped = [m for g in groups for m in g["modules"]]
check(len(groups) > 1 and sorted(grouped) == mods,
      "all modules are grouped (%d groups)" % len(groups),
      "ungrouped: %s" % ",".join(sorted(set(mods) - set(grouped))[:5]))
check(not any(g["label"] == "Other" for g in groups), 'no catch-all "Other" group')

IMP = {"access", "analyze", "capture", "check", "convert", "create", "delete",
       "download", "execute", "extract", "fetch", "find", "get", "list",
       "lookup", "merge", "monitor", "parse", "perform", "pull", "retrieve",
       "search", "split", "submit", "upload", "validate"}
descbad = []
for m in mods:
    md = load(m, "metadata.json")
    d = (md.get("description") or "").strip()
    lbl = md.get("label", "")
    if not d:
        descbad.append("%s: empty" % m)
    elif d != md["description"]:
        descbad.append("%s: whitespace" % m)
    elif not d.endswith((".", "!", "?")):
        descbad.append("%s: no period" % m)
    elif d.split()[0].lower() in IMP:
        descbad.append("%s: imperative" % m)
    elif d.rstrip(".").lower() == lbl.lower():
        descbad.append("%s: restates label" % m)
check(not descbad, "descriptions are third person, sentence case, end with a period",
      "; ".join(descbad[:6]))

BAD_LABELS = {"Ip", "Apikey", "Api Key", "Lang", "Domainname", "File Id", "Ips",
              "Uastrings", "Url", "Lat", "Long", "Ip Address"}
found = set()
for m in mods:
    for p in load(m, "expect.imljson"):
        if p.get("label") in BAD_LABELS:
            found.add("%s.%s" % (m, p["label"]))
check(not found, "parameter labels are humanized (IP, API key, URL, Latitude...)",
      ",".join(sorted(found)[:6]))

print("\n".join(info))
if fail:
    print("\n" + "\n".join(fail))
    print("\n%d checks passed, %d FAILED" % (len(info), len(fail)))
    sys.exit(1)
print("\nAll %d checks passed." % len(info))
