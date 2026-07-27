#!/usr/bin/env python3
"""
Generate a Make.com custom-app folder tree from the APIFreaks OpenAPI spec.

Usage:
    python3 generate_make_app.py apifreaks-openapi.json ./make-app

This is the v2 generator. Compared with the first draft it produces a
review-ready app:

  * output interfaces built from the real response schemas (every module)
  * search modules (typeId 9) with iterate / output {{item}} / limit
  * pagination directive for endpoints that page results
  * headers wired for User-Agent, Accept-Language, X-Webhook-Authorization
  * no "format" (json/xml) selector - the XML branch silently broke output
  * connection secret stored as a password field, tested against a free endpoint
  * binary upload (buffer / multipart / octet-stream) and binary download
  * real module groups, humanized parameter labels, sentence-case descriptions
  * the hand-authored universal "Make an API Call" module (relative path only)

Everything derivable is derived from the spec; the small amount that isn't
(group names, a few awkward labels, V1/V2 legacy flags) lives in the config
block near the top of this file.
"""

import json
import os
import re
import sys

BASE_URL = "https://api.apifreaks.com"
AUTH_HEADER = "X-apiKey"
CONNECTION = "apifreaks"

TYPE_ACTION = 4
TYPE_SEARCH = 9

# ---------------------------------------------------------------------------
# Config that cannot be derived from the spec
# ---------------------------------------------------------------------------

# OpenAPI tag -> Make group label. Order here is the order shown in the GUI.
GROUP_ORDER = [
    "IP Geolocation", "WHOIS", "DNS", "Domain", "SSL", "Geocoding", "GeoDB",
    "ZIP Code", "Currency", "Commodity", "Financial", "Weather", "Timezone",
    "Astronomy", "Email & Phone Validation", "User Agent", "Readability",
    "OCR", "Web Scraping", "Screenshot", "PDF", "General",
]
GROUP_MAP = {
    "IP Geolocation": "IP Geolocation", "WHOIS": "WHOIS", "DNS": "DNS",
    "Domain": "Domain", "SSL": "SSL", "Geocoding": "Geocoding", "GeoDB": "GeoDB",
    "ZIP Code": "ZIP Code", "Currency": "Currency", "Commodity": "Commodity",
    "Financial": "Financial", "Weather": "Weather", "Timezone": "Timezone",
    "Other": "Astronomy", "Email Validation": "Email & Phone Validation",
    "Phone Validation": "Email & Phone Validation", "User Agent": "User Agent",
    "Readability": "Readability", "OCR": "OCR", "Web Scraping": "Web Scraping",
    "Screenshot": "Screenshot", "PDF": "PDF", "General": "General",
}

# The universal module is not part of the spec; place it in General.
MAKE_API_CALL = "makeApiCall"

# Older V1 modules kept for back-compat but flagged "(legacy)".
LEGACY_V1 = {
    "bulkIpLookup", "getGeolocationLookup", "getGeolocationAstronomy",
    "getTimezone", "whoisLookup", "postDomainWhoisLive",
}

# Search modules (reviewer list). Value = container to iterate; None = root body.
SEARCH_ITERATE = {
    "bulkIpLookup": None, "bulkIpLookupV2": None, "bulkIpSecurityLookup": None,
    "getFlagsSupported": None, "getGeocoderSearch": None, "getSwiftCodeFinder": None,
    "getVatRatesCountry": None, "getVatRatesIpAddress": None,
    "postPhoneValidationBulk": None, "postUserAgentLookup": None,
}

# Paginated search modules -> (list container, page qs key, currentPage field, totalPages field)
PAGINATED = {
    "dnsHistoryLookup": ("historicalDnsRecords", "page", "currentPage", "totalPages"),
    "getDomainWhoisReverse": ("whois_domains_historical", "page", "current_Page", "total_Pages"),
    "getSubdomainsLookup": ("subdomains", "page", "current_page", "total_pages"),
    "reverseDnsLookup": ("reverseDnsRecords", "page", "currentPage", "totalPages"),
    "searchZipByCity": ("codes", "page", "current_page", "total_pages"),
    "searchZipByRadius": ("results", "page", "current_page", "total_pages"),
    "searchZipByRegion": ("codes", "page", "current_page", "total_pages"),
}

# Binary download modules -> IML expression for the output file name.
BINARY_DOWNLOAD = {
    "getPdfResourceDownload": "{{parameters.resourceId}}",
    "websiteScreenshot": "{{ifempty(parameters.resultFileName, 'screenshot')}}",
    "getFlags": "{{parameters.name}}",
}

# Module renamed to avoid a misleading internal name (weather vs currency time-series).
RENAME = {"getTimeSeries2": "getWeatherTimeSeries"}

# Params never surfaced to the user (the connection already carries the key).
DROP_PARAMS = {"apiKey", "apikey"}

# Curated module labels where the auto-derived one reads poorly.
LABEL_OVERRIDES = {
    "getGeolocationLookup": "Get IP geolocation (legacy)",
    "getGeolocationLookupV2": "Get IP geolocation",
    "bulkIpLookup": "Bulk IP geolocation lookup (legacy)",
    "bulkIpLookupV2": "Bulk IP geolocation lookup",
    "getIpSecurity": "Get IP security data",
    "bulkIpSecurityLookup": "Bulk IP security lookup",
    "getGeolocationAstronomy": "Get astronomy data (legacy)",
    "getGeolocationAstronomyV2": "Get astronomy data",
    "getTimezone": "Get timezone by IP (legacy)",
    "getTimezoneV2": "Get timezone by IP",
    "convertTimezone": "Convert time between timezones",
    "whoisLookup": "Get domain WHOIS (legacy)",
    "whoisLookupV2": "Get domain WHOIS",
    "postDomainWhoisLive": "Bulk domain WHOIS (legacy)",
    "postDomainWhoisLiveV2": "Bulk domain WHOIS",
    "whoisHistoryLookup": "Get domain WHOIS history",
    "getDomainWhoisReverse": "Search reverse domain WHOIS",
    "getIpWhoisLive": "Get IP WHOIS",
    "getAsnWhoisLive": "Get ASN WHOIS",
    "bulkDnsLookup": "Bulk DNS lookup",
    "dnsLookup": "Get DNS records",
    "dnsHistoryLookup": "Search DNS history",
    "reverseDnsLookup": "Search reverse DNS records",
    "getDomainAvailability": "Check domain availability",
    "postDomainAvailability": "Check domain availability in bulk",
    "getDomainAvailabilitySuggestions": "Suggest available domains",
    "getSubdomainsLookup": "Search subdomains",
    "sslCertificateLookup": "Get SSL certificate",
    "sslCertificateChainLookup": "Get SSL certificate chain",
    "getGeocoderSearch": "Search addresses (forward geocoding)",
    "getGeocoderReverse": "Reverse geocode coordinates",
    "postEmailValidationSingle": "Validate an email address",
    "postEmailValidationBulk": "Validate emails in bulk",
    "postPhoneValidation": "Validate a phone number",
    "postPhoneValidationBulk": "Search validated phone numbers",
    "getUserAgentLookup": "Look up a user agent",
    "postUserAgentLookup": "Look up user agents in bulk",
    "getVatValidation": "Validate a VAT number",
    "getVatRatesCountry": "Search VAT rates by country",
    "getVatRatesIpAddress": "Search VAT rates by IP address",
    "postVatRatesCountry": "Get VAT rates for countries",
    "getVatSupportedCountries": "List VAT-supported countries",
    "getIbanValidation": "Validate an IBAN",
    "getSwiftCodeFinder": "Search SWIFT codes",
    "getSwiftCodeLookup": "Get SWIFT code details",
    "getFlags": "Get country flags",
    "getFlagsSupported": "List supported flags",
    "getSubregionsByRegion": "List subregions by region",
    "getCreditsUsageInfo": "Get credits usage information",
    "performScraping": "Scrape a web page",
    "ocrPredict": "Extract text with OCR",
    "websiteScreenshot": "Capture a website screenshot",
    "bulkScreenshot": "Capture website screenshots in bulk",
    "getTimeSeries": "Get currency time series",
    "getWeatherTimeSeries": "Get weather time series",
    "postCurrent": "Get current weather in bulk",
    "postPdfResourceUpload": "Upload PDF files",
    "postPdfResourceUploadBinary": "Upload a PDF (binary)",
    "getPdfResourceDownload": "Download a processed file",
    "getPdfTaskStatus": "Get PDF task status",
    "getPdfFileStatus": "Get PDF file status",
    "getPdfFiles": "List uploaded PDF files",
    "deletePdfFile": "Delete an uploaded PDF file",
    "postPdfMerge": "Merge PDF files",
    "postPdfSplit": "Split a PDF",
    "postPdfCompress": "Compress a PDF",
    "postPdfRotate": "Rotate PDF pages",
    "postPdfExtractPages": "Extract PDF pages",
    "postPdfRemovePages": "Remove PDF pages",
    "postPdfLinearize": "Linearize a PDF",
    "postPdfEncrypt": "Encrypt a PDF",
    "postPdfDecrypt": "Decrypt a PDF",
    "postPdfRestrict": "Restrict a PDF",
    "postPdfUnrestrict": "Remove PDF restrictions",
    "postPdfPng": "Convert a PDF to PNG",
    "postPdfJpg": "Convert a PDF to JPG",
    "postPdfTif": "Convert a PDF to TIFF",
    "postPdfBmp": "Convert a PDF to BMP",
    "postPdfGif": "Convert a PDF to GIF",
    "getCurrent": "Get current weather",
    "getForecast": "Get weather forecast",
    "getHistorical": "Get historical weather",
    "getMarine": "Get marine weather",
    "getFlood": "Get flood data",
    "getAirQuality": "Get air quality",
    "convertByIp": "Convert currency by IP",
    "convertHistorical": "Convert currency (historical)",
    "convertLatest": "Convert currency (latest)",
    "getFluctuation": "Get currency fluctuation",
    "getSupportedCurrencies": "List supported currencies",
    "getCurrencySymbols": "List currency symbols",
    "getCommoditySymbols": "List commodity symbols",
    "getCommodityFluctuation": "Get commodity fluctuation",
    "getAdminUnits": "List administrative levels",
    "getGeoAdminUnits": "List administrative units",
    "getGeoAdminUnitDetails": "Get administrative unit details",
    "getGeoCities": "List cities",
    "getGeoRegions": "List regions",
    "getCountries": "List countries",
    "lookupZipCodes": "Look up ZIP codes",
    "bulklookupZipCodesPost": "Look up ZIP codes in bulk",
    "getZipcodeDistance": "Get distance between ZIP codes",
    "getZipcodeDistanceMatch": "Match ZIP codes by distance",
    "grammarCorrect": "Correct grammar",
    "grammarDetect": "Detect grammar errors",
    "readabilityScore": "Score readability",
    "weakWordsDetect": "Detect weak words",
}

# Curated descriptions where the spec text is imperative / just restates the label.
DESC_OVERRIDES = {
    "getGeoRegions": "Returns the list of regions available in the GeoDB dataset.",
    "getSubregionsByRegion": "Returns the subregions that belong to a given region.",
    "lookupZipCodes": "Returns ZIP/postal code details for the supplied query.",
    "getAdminUnits": "Returns the administrative levels available in the GeoDB dataset.",
    "getGeoAdminUnits": "Returns the administrative units available in the GeoDB dataset.",
    "getCountryDetails": "Returns detailed information about a country in the GeoDB dataset.",
}

# ---------------------------------------------------------------------------
# Label / identifier helpers
# ---------------------------------------------------------------------------

# lowercase token -> replacement (keeps abbreviations correct after sentence-casing)
ABBR = {
    "ip": "IP", "ips": "IP addresses", "url": "URL", "urls": "URLs", "uri": "URI",
    "api": "API", "apikey": "API key", "dns": "DNS", "ssl": "SSL", "tls": "TLS",
    "vat": "VAT", "iban": "IBAN", "swift": "SWIFT", "bic": "BIC", "ocr": "OCR",
    "pdf": "PDF", "zip": "ZIP", "id": "ID", "ids": "IDs", "asn": "ASN",
    "whois": "WHOIS", "geodb": "GeoDB", "html": "HTML", "css": "CSS", "js": "JS",
    "ua": "user agent", "uastrings": "user agent strings", "lang": "language",
    "lat": "latitude", "long": "longitude", "lng": "longitude", "tld": "TLD",
    "poi": "POI", "dma": "DMA", "eu": "EU", "os": "OS", "http": "HTTP",
    "domainname": "domain name", "ttl": "TTL", "xml": "XML", "json": "JSON",
    "mx": "MX", "ns": "NS", "txt": "TXT", "aaaa": "AAAA", "cidr": "CIDR",
    "isp": "ISP", "gps": "GPS", "utc": "UTC", "sla": "SLA", "sku": "SKU",
}


def _split_words(name):
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name or "")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
    name = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", name)
    return [p for p in re.split(r"[^A-Za-z0-9]+", name) if p]


def labelize(name):
    """Human, sentence-case label with correct abbreviations."""
    words = _split_words(name)
    out = []
    for w in words:
        lw = w.lower()
        if lw in ABBR:
            out.append(ABBR[lw])
        elif len(w) > 1 and w.isupper():
            out.append(w)
        else:
            out.append(lw)
    if not out:
        return name
    s = " ".join(out)
    return s[0].upper() + s[1:]


def ident(name):
    """Safe IML identifier for a parameter name (keeps the wire key separate)."""
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name or "") if p]
    if not parts:
        return "param"
    s = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    if s[0].isdigit():
        s = "_" + s
    return s


def slug(text):
    parts = [p for p in re.split(r"[^a-zA-Z0-9]+", text or "") if p]
    if not parts:
        return "operation"
    name = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return name[0].lower() + name[1:]


def module_label(opid, name):
    if name in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[name]
    base = re.sub(r"V\d+$", "", opid or name)
    lbl = labelize(base)
    if name in LEGACY_V1:
        lbl += " (legacy)"
    return lbl


def third_person(verb):
    """English third-person singular of a lowercase imperative verb."""
    if verb.endswith("y") and verb[-2:-1] not in "aeiou":
        return verb[:-1] + "ies"
    if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
        return verb + "es"
    return verb + "s"


# Spec descriptions are written as instructions ("Retrieve the ..."); Make wants
# third person. "get"/"retrieve" read better as "Returns" than "Gets"/"Retrieves".
IMPERATIVE_MAP = {"get": "Returns", "retrieve": "Returns", "lookup": "Looks up"}

IMPERATIVE_VERBS = {
    "access", "add", "analyze", "apply", "build", "calculate", "capture",
    "check", "compare", "compress", "convert", "correct", "create", "decrypt",
    "delete", "detect", "determine", "discover", "download", "encrypt",
    "execute", "extract", "fetch", "find", "generate", "identify", "linearize",
    "list", "match", "merge", "monitor", "obtain", "parse", "perform",
    "provide", "pull", "query", "read", "remove", "restrict", "return",
    "rotate", "run", "score", "scrape", "search", "send", "split", "submit",
    "suggest", "take", "track", "translate", "unrestrict", "upload", "use",
    "validate", "verify",
}


def to_third_person(text):
    """Rewrite a leading imperative verb as third-person singular."""
    m = re.match(r"([A-Za-z]+)(\b.*)", text, re.S)
    if not m:
        return text
    head, rest = m.group(1), m.group(2)
    low = head.lower()
    if low in IMPERATIVE_MAP:
        return IMPERATIVE_MAP[low] + rest
    if low in IMPERATIVE_VERBS:
        word = third_person(low)
        return word[0].upper() + word[1:] + rest
    return text


def clean_desc(text, label, name):
    if name in DESC_OVERRIDES:
        return DESC_OVERRIDES[name]
    if not text:
        text = label
    text = re.sub(r"\s+", " ", text.replace("\r", " ").replace("\n", " ")).strip()
    text = to_third_person(text)
    if text and text[-1] not in ".!?":
        text += "."
    return text


# ---------------------------------------------------------------------------
# Spec helpers
# ---------------------------------------------------------------------------

def resolve(spec, node):
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 20:
        ref = node["$ref"].lstrip("#/").split("/")
        target = spec
        for part in ref:
            target = target.get(part, {})
        node = target
        seen += 1
    return node


def scalar_type(schema):
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if t == "string":
        if schema.get("format") in ("date", "date-time"):
            return "date"
        return "text"
    if t in ("integer", "number"):
        return "number"
    if t == "boolean":
        return "boolean"
    return "text"


def make_input_type(schema):
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    return {
        "string": "text", "integer": "number", "number": "number",
        "boolean": "boolean", "array": "array", "object": "collection",
    }.get(t, "text")


# ---------------------------------------------------------------------------
# Interface generation
# ---------------------------------------------------------------------------

def iface_field(spec, name, schema, depth=0):
    schema = resolve(spec, schema)
    field = {"name": name, "label": labelize(name)}
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if t == "object" and depth < 8:
        props = schema.get("properties") or {}
        field["type"] = "collection"
        field["spec"] = [iface_field(spec, k, v, depth + 1) for k, v in props.items()]
        return field
    if t == "array" and depth < 8:
        items = resolve(spec, schema.get("items") or {})
        it = items.get("type")
        if isinstance(it, list):
            it = next((x for x in it if x != "null"), "string")
        field["type"] = "array"
        if it == "object":
            props = items.get("properties") or {}
            field["spec"] = [iface_field(spec, k, v, depth + 1) for k, v in props.items()]
        else:
            field["spec"] = {"type": scalar_type(items), "label": labelize(name)}
        return field
    field["type"] = scalar_type(schema)
    return field


def response_schema(spec, op):
    resp = op.get("responses", {})
    ok = resp.get("200") or resp.get("201") or (next(iter(resp.values())) if resp else {})
    ok = resolve(spec, ok)
    schema = ok.get("schema")
    if schema is None:
        content = ok.get("content", {})
        media = content.get("application/json") or (next(iter(content.values())) if content else {})
        schema = media.get("schema", {}) if isinstance(media, dict) else {}
    return resolve(spec, schema)


def build_interface(spec, schema, iterate_container):
    schema = resolve(spec, schema)
    if not isinstance(schema, dict) or not schema:
        return []
    # Search module: describe the item shape.
    if iterate_container is not None:
        if iterate_container == "__root__":
            items = resolve(spec, schema.get("items") or {})
        else:
            cont = resolve(spec, (schema.get("properties") or {}).get(iterate_container) or {})
            items = resolve(spec, cont.get("items") or {})
        props = items.get("properties") or {}
        if props:
            return [iface_field(spec, k, v) for k, v in props.items()]
        # scalar list
        return [{"name": "value", "label": "Value", "type": scalar_type(items)}]
    # Action module.
    if schema.get("type") == "array":
        items = resolve(spec, schema.get("items") or {})
        props = items.get("properties") or {}
        return [iface_field(spec, k, v) for k, v in props.items()]
    props = schema.get("properties") or {}
    return [iface_field(spec, k, v) for k, v in props.items()]


BINARY_INTERFACE = [
    {"name": "name", "label": "File name", "type": "filename", "semantic": "file:name"},
    {"name": "data", "label": "Data", "type": "buffer", "semantic": "file:data"},
]


# ---------------------------------------------------------------------------
# Parameter (expect) generation
# ---------------------------------------------------------------------------

def param_entry(spec, p):
    p = resolve(spec, p)
    schema = resolve(spec, p.get("schema", {})) if p.get("schema") else p
    orig = p.get("name")
    entry = {
        "name": ident(orig),
        "label": labelize(orig),
        "type": make_input_type(schema) if schema else "text",
        "required": bool(p.get("required", False)),
    }
    if p.get("description"):
        entry["help"] = re.sub(r"\s+", " ", p["description"].strip())
    enum = (schema.get("enum") if isinstance(schema, dict) else None) or p.get("enum")
    if enum:
        entry["type"] = "select"
        entry["options"] = [{"label": str(v), "value": v} for v in enum]
    return entry


def body_prop_entry(spec, name, prop, required):
    prop = resolve(spec, prop)
    entry = {
        "name": ident(name),
        "label": labelize(name),
        "type": make_input_type(prop),
        "required": name in required,
    }
    if prop.get("description"):
        entry["help"] = re.sub(r"\s+", " ", prop["description"].strip())
    enum = prop.get("enum")
    if enum:
        entry["type"] = "select"
        entry["options"] = [{"label": str(v), "value": v} for v in enum]
    return entry


def json_body_props(spec, op):
    """Return (properties dict, required set) for an application/json request body."""
    rb = op.get("requestBody")
    if not rb:
        return {}, set()
    rb = resolve(spec, rb)
    content = rb.get("content", {})
    media = content.get("application/json")
    if not media:
        return {}, set()
    schema = resolve(spec, media.get("schema", {}))
    return (schema.get("properties") or {}), set(schema.get("required", []))


# ---------------------------------------------------------------------------
# Module builder
# ---------------------------------------------------------------------------

def build_module(spec, name, path, method, op, tag):
    method = method.upper()
    params = [resolve(spec, p) for p in op.get("parameters", [])]
    path_params = [p for p in params if p.get("in") == "path"]
    query_params = [p for p in params if p.get("in") == "query"
                    and p.get("name") not in DROP_PARAMS
                    and not _is_response_format(spec, p)]
    header_params = [p for p in params if p.get("in") == "header" and p.get("name") != AUTH_HEADER]

    if name in PAGINATED:
        pag_key = PAGINATED[name][1]
        query_params = [p for p in query_params if p.get("name") != pag_key]

    expect = []
    api = {"url": path, "method": method}
    for pp in path_params:
        api["url"] = api["url"].replace("{%s}" % pp["name"], "{{parameters.%s}}" % ident(pp["name"]))
        expect.append(param_entry(spec, pp))

    qs = {}
    for q in query_params:
        qs[q["name"]] = "{{parameters.%s}}" % ident(q["name"])
        expect.append(param_entry(spec, q))

    headers = {}
    for h in header_params:
        headers[h["name"]] = "{{parameters.%s}}" % ident(h["name"])
        expect.append(param_entry(spec, h))

    # ---- request body / file handling ----------------------------------
    # ocrPredict already exposes url/model/etc as query params (added above);
    # it just needs the alternative file-upload input, so it takes the
    # multipart path too.
    is_octet = name == "postPdfResourceUploadBinary"
    is_multipart_upload = _has_multipart_file(spec, op)

    if is_octet:
        if not any(p.get("name") == "fileName" for p in expect):
            expect.append({"name": "fileName", "label": "File name", "type": "filename",
                           "required": True, "semantic": "file:name",
                           "help": "Name to store the uploaded PDF under."})
        else:
            # the spec's file_name query param already exists; enrich it as a filename input
            for p in expect:
                if p.get("name") == "fileName":
                    p["type"] = "filename"
                    p["semantic"] = "file:name"
                    p["required"] = True
        expect.append({"name": "fileData", "label": "File", "type": "buffer",
                       "required": True, "semantic": "file:data",
                       "help": "The PDF file to upload, in binary form."})
        qs.setdefault("file_name", "{{parameters.fileName}}")
        api["body"] = "{{parameters.fileData}}"
        api["type"] = "binary"
        headers["Content-Type"] = "application/octet-stream"
    elif is_multipart_upload:
        if name == "ocrPredict":
            data_help = "Image, PDF, or ZIP to OCR. Provide this or a URL."
        else:
            data_help = ("The file to process. Leave empty to use a previously "
                         "uploaded file referenced by File ID.")
        expect.append({"name": "fileName", "label": "File name", "type": "filename",
                       "required": False, "semantic": "file:name",
                       "help": "Name of the file being uploaded."})
        expect.append({"name": "fileData", "label": "File", "type": "buffer",
                       "required": False, "semantic": "file:data",
                       "help": data_help})
        api["body"] = {"file": {"value": "{{parameters.fileData}}",
                                "options": {"filename": "{{parameters.fileName}}"}}}
        api["type"] = "multipart/form-data"
    else:
        props, required = json_body_props(spec, op)
        if props and method in ("POST", "PUT", "PATCH"):
            body = {}
            for pname, prop in props.items():
                body[pname] = "{{parameters.%s}}" % ident(pname)
                expect.append(body_prop_entry(spec, pname, prop, required))
            api["body"] = body

    if qs:
        api["qs"] = qs
    if headers:
        api["headers"] = headers

    # ---- response / interface -----------------------------------------
    schema = response_schema(spec, op)
    is_search = name in SEARCH_ITERATE or name in PAGINATED
    is_download = name in BINARY_DOWNLOAD

    if is_download:
        api["response"] = {
            "type": "binary",
            "output": {"name": BINARY_DOWNLOAD[name], "data": "{{body}}"},
        }
        interface = list(BINARY_INTERFACE)
        type_id = TYPE_ACTION
    elif is_search:
        container = _iterate_container(name)
        interface = build_interface(spec, schema, _iterate_container_ref(name))
        # When the list items are primitives (not objects), {{item}} is a bare
        # value; wrap it so it matches the "value" interface field.
        scalar_items = len(interface) == 1 and interface[0].get("name") == "value"
        api["response"] = {
            "iterate": container,
            "output": {"value": "{{item}}"} if scalar_items else "{{item}}",
            "limit": "{{parameters.limit}}",
        }
        if name in PAGINATED:
            _, pag_key, cur, tot = PAGINATED[name]
            api["pagination"] = {
                "qs": {pag_key: "{{pagination.page}}"},
                "condition": "{{body.%s < body.%s}}" % (cur, tot),
            }
        if not any(p.get("name") == "limit" for p in expect):
            expect.append({
                "name": "limit", "label": "Limit", "type": "uinteger", "default": 10,
                "help": "Maximum number of results to return.",
            })
        type_id = TYPE_SEARCH
    else:
        api["response"] = {"output": "{{body}}"}
        interface = build_interface(spec, schema, None)
        type_id = TYPE_ACTION

    label = module_label(op.get("operationId") or name, name)
    description = clean_desc(op.get("description") or op.get("summary"), label, name)
    metadata = {
        "name": name, "label": label, "description": description,
        "connection": CONNECTION, "typeId": type_id,
    }
    return metadata, api, expect, interface


def _is_response_format(spec, p):
    """True for the json/xml response-format selector (dropped), False for a
    meaningful format such as the image format on the flags endpoint (kept)."""
    if p.get("name") != "format":
        return False
    schema = resolve(spec, p.get("schema", {})) if p.get("schema") else {}
    enum = set(schema.get("enum") or p.get("enum") or [])
    if not enum:
        return True
    return enum <= {"json", "xml"}


def _has_multipart_file(spec, op):
    rb = op.get("requestBody")
    if not rb:
        return False
    rb = resolve(spec, rb)
    mp = (rb.get("content") or {}).get("multipart/form-data")
    if not mp:
        return False
    schema = resolve(spec, mp.get("schema", {}))
    return "file" in (schema.get("properties") or {})


def _iterate_container(name):
    if name in PAGINATED:
        return "{{body.%s}}" % PAGINATED[name][0]
    cont = SEARCH_ITERATE.get(name)
    return "{{body}}" if cont is None else "{{body.%s}}" % cont


def _iterate_container_ref(name):
    if name in PAGINATED:
        return PAGINATED[name][0]
    cont = SEARCH_ITERATE.get(name)
    return "__root__" if cont is None else cont


# ---------------------------------------------------------------------------
# The hand-authored universal module
# ---------------------------------------------------------------------------

def make_api_call_files():
    metadata = {
        "name": MAKE_API_CALL,
        "label": "Make an API Call",
        "description": "Performs an authenticated call to any APIFreaks endpoint using a "
                       "relative path. Covers endpoints that do not yet have a dedicated module.",
        "connection": CONNECTION,
        "typeId": TYPE_ACTION,
    }
    api = {
        "url": "{{parameters.url}}",
        "method": "{{parameters.method}}",
        "qs": "{{toCollection(parameters.qs, 'key', 'value')}}",
        "headers": "{{toCollection(parameters.headers, 'key', 'value')}}",
        "body": "{{parameters.body}}",
        "response": {
            "output": {
                "statusCode": "{{statusCode}}",
                "headers": "{{headers}}",
                "body": "{{body}}",
            }
        },
    }
    expect = [
        {"name": "url", "label": "URL", "type": "text", "required": True,
         "help": "Relative path only, e.g. /v1.0/geolocation/lookup. The base URL "
                 "(https://api.apifreaks.com) is added automatically."},
        {"name": "method", "label": "Method", "type": "select", "required": True,
         "default": "GET", "options": [
             {"label": "GET", "value": "GET"}, {"label": "POST", "value": "POST"},
             {"label": "PUT", "value": "PUT"}, {"label": "PATCH", "value": "PATCH"},
             {"label": "DELETE", "value": "DELETE"}]},
        {"name": "qs", "label": "Query string", "type": "array", "spec": [
            {"name": "key", "label": "Key", "type": "text"},
            {"name": "value", "label": "Value", "type": "text"}]},
        {"name": "headers", "label": "Headers", "type": "array",
         "help": "Extra request headers. Authorization is already handled by the connection.",
         "spec": [
             {"name": "key", "label": "Key", "type": "text"},
             {"name": "value", "label": "Value", "type": "text"}]},
        {"name": "body", "label": "Body", "type": "any",
         "help": "Request body for POST/PUT/PATCH calls."},
    ]
    interface = [
        {"name": "statusCode", "label": "Status code", "type": "number"},
        {"name": "headers", "label": "Headers", "type": "collection", "spec": []},
        {"name": "body", "label": "Body", "type": "collection", "spec": []},
    ]
    return metadata, api, expect, interface


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

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
        "description": (spec.get("info", {}) or {}).get(
            "description", "APIFreaks API hub."),
    })
    write(os.path.join(out_dir, "base.imljson"), {
        "baseUrl": BASE_URL,
        "headers": {AUTH_HEADER: "{{connection.apiKey}}"},
        "response": {"error": {
            "message": "[{{statusCode}}] {{ifempty(body.message, ifempty(body.error, body))}}"}},
        "log": {"sanitize": ["request.headers.%s" % AUTH_HEADER]},
    })
    conn = os.path.join(out_dir, "connections", CONNECTION)
    write(os.path.join(conn, "metadata.json"),
          {"name": CONNECTION, "label": "APIFreaks connection", "type": "apikey"})
    # Test against a free, always-available endpoint (no credit consumption).
    write(os.path.join(conn, "api.imljson"), {
        "url": BASE_URL + "/v1.0/credits/usage/info", "method": "GET",
        "headers": {AUTH_HEADER: "{{parameters.apiKey}}"},
        "response": {"error": {"message": "[{{statusCode}}] Invalid API key"}},
        "log": {"sanitize": ["request.headers.%s" % AUTH_HEADER]},
    })
    write(os.path.join(conn, "parameters.imljson"),
          [{"name": "apiKey", "type": "password", "label": "API key", "required": True}])

    # ---- modules ----
    count = 0
    seen = set()
    groups = {g: [] for g in GROUP_ORDER}
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
            name = RENAME.get(name, name)

            tag = (op.get("tags") or ["General"])[0]
            metadata, api, expect, interface = build_module(spec, name, path, method, op, tag)

            mod_dir = os.path.join(out_dir, "modules", name)
            os.makedirs(mod_dir, exist_ok=True)
            write(os.path.join(mod_dir, "metadata.json"), metadata)
            write(os.path.join(mod_dir, "api.imljson"), api)
            write(os.path.join(mod_dir, "expect.imljson"), expect)
            write(os.path.join(mod_dir, "interface.imljson"), interface)
            write(os.path.join(mod_dir, "samples.imljson"), {})

            group = GROUP_MAP.get(tag, "General")
            groups.setdefault(group, []).append(name)
            count += 1

    # ---- universal module ----
    metadata, api, expect, interface = make_api_call_files()
    mod_dir = os.path.join(out_dir, "modules", MAKE_API_CALL)
    os.makedirs(mod_dir, exist_ok=True)
    write(os.path.join(mod_dir, "metadata.json"), metadata)
    write(os.path.join(mod_dir, "api.imljson"), api)
    write(os.path.join(mod_dir, "expect.imljson"), expect)
    write(os.path.join(mod_dir, "interface.imljson"), interface)
    write(os.path.join(mod_dir, "samples.imljson"), {})
    groups["General"].append(MAKE_API_CALL)
    count += 1

    # ---- groups ----
    groups_out = [{"label": g, "modules": groups[g]} for g in GROUP_ORDER if groups.get(g)]
    write(os.path.join(out_dir, "groups.json"), groups_out)

    print("Generated %d modules into %s/modules/" % (count, out_dir))
    print("Groups: %s" % ", ".join(g["label"] for g in groups_out))


if __name__ == "__main__":
    main()
