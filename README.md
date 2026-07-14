# Using APIFreaks on Make

Connect the **APIFreaks** app to your Make scenarios to add IP intelligence, WHOIS,
DNS, geocoding, weather, currency, PDF tools, and more — all with point‑and‑click
modules, no code. This guide walks you from zero to your first working scenario.

- Website: https://apifreaks.com
- Get a free API key: https://apifreaks.com/signup
- API docs: https://apifreaks.com/docs
- Support: support@apifreaks.com

---

## 1. What you need

1. A **Make account** — https://www.make.com
2. An **APIFreaks API key** — sign up free at https://apifreaks.com/signup, then
   copy your key from your **Dashboard → API Keys** (https://apifreaks.com/dashboard).
   The free tier includes credits to get started; paid plans add volume and
   premium data. See https://apifreaks.com/pricing.

---

## 2. Add an APIFreaks module to a scenario

1. In Make, open or create a **Scenario**.
2. Click the **+** to add a module.
3. Search for **APIFreaks** and select it.
4. Choose the action you want (for example, *Get IP Geolocation*). Modules are
   labelled by category, e.g. `IP Geolocation: …`, `WHOIS: …`, `Weather: …`, so
   you can type a category name to filter.

## 3. Create your connection (once)

The first time you add an APIFreaks module, Make asks you to create a connection:

1. Click **Create a connection**.
2. Give it a name (e.g. "My APIFreaks key").
3. Paste your **API Key** into the field.
4. Click **Save**. Make validates the key immediately.

Your key is sent securely on every request and is hidden from execution logs. The
same connection works for **every** APIFreaks module across all your scenarios —
you only set it up once.

## 4. Fill in the fields and run

1. Select the fields the module needs (required fields are marked). You can type a
   value directly or **map** a value from an earlier module (e.g. an IP address
   coming from a webhook or a spreadsheet cell).
2. Optional settings usually live under **Show advanced settings**.
3. Click **Run once** to test. The module returns structured data you can map into
   any downstream module (Google Sheets, Slack, a database, an email, etc.).

---

## 5. Action vs. Search modules

- **Action** modules return a single result — e.g. *Get IP Geolocation* for one IP.
- **Search** modules return a list of results and let downstream modules iterate
  over each item — e.g. the **bulk** lookups that accept many inputs at once.

Both behave like any native Make module: their output fields appear in the mapping
panel of later modules.

## 6. Need an endpoint that isn't a dedicated module?

Use **Make an API Call** — a universal APIFreaks module. Enter the endpoint path
(for example `/v1.0/geolocation/lookup`), pick the method, and add any query
parameters. It uses your existing connection and returns the raw response, so you
can reach any APIFreaks endpoint even before a dedicated module exists.

---

## 7. What you can do (module categories)

| Category | Modules | What it does |
|---|---|---|
| IP Geolocation | 6 | Geolocation + threat/security (VPN, proxy, Tor) for IPv4/IPv6, single & bulk |
| WHOIS | 8 | Domain / IP / ASN WHOIS, plus history, reverse and bulk lookups |
| DNS | 4 | Live, historical, reverse and bulk DNS records (A, AAAA, MX, TXT, NS…) |
| Domain | 4 | Availability, bulk availability, name suggestions, subdomain discovery |
| SSL | 2 | SSL certificate and certificate‑chain details for any domain |
| Geocoding | 2 | Forward (address → coordinates) and reverse geocoding |
| GeoDB | 10 | Countries, regions, subregions, administrative units, cities, flags |
| ZIP Code | 7 | Lookup and search postal codes by city, region, radius or distance |
| Currency | 10 | Live & historical exchange rates, conversion, time series, fluctuation |
| Commodity | 5 | Live & historical commodity prices, time series, fluctuation, symbols |
| Financial | 8 | VAT rates & validation, IBAN validation, SWIFT lookup |
| Weather | 8 | Current, forecast, historical, marine, air quality and flood data |
| Timezone | 3 | Timezone lookup and time conversion by IP, coordinates or city |
| Astronomy (Other) | 2 | Sunrise, sunset, moon phase and celestial positions |
| Email Validation | 2 | Validate single or multiple email addresses |
| Phone Validation | 2 | Validate format, carrier, line type, geolocation and risk |
| User Agent | 2 | Parse browser, device and OS details from user‑agent strings |
| Readability | 4 | Grammar detect/correct, weak‑word detection, readability scoring |
| OCR | 1 | Extract text from images, PDFs or ZIP archives |
| Web Scraping | 1 | Scrape any page with custom instructions |
| Screenshot | 2 | Capture website screenshots, single & bulk |
| PDF | 23 | Merge, split, rotate, compress, convert, encrypt/decrypt, upload/download |
| General | 1 | Check your remaining API credit usage |

That's **118 modules** in total, including the universal *Make an API Call*.

---

## 8. Example scenarios

**Enrich new signups with location.**
Webhook (new user) → *IP Geolocation: Get IP Geolocation* → Google Sheets (add row
with country, city, ISP).

**Fraud screening on orders.**
Webhook (order) → *IP Geolocation* with security enabled → Filter (block if VPN/
proxy/high threat score) → route flagged orders to a review channel.

**Daily FX snapshot.**
Schedule (daily) → *Currency: Get the latest exchange rates* → append to a sheet /
post to Slack.

**Domain due diligence.**
Google Sheets (read domains) → *WHOIS: Bulk domain WHOIS* → write registrar,
creation and expiry dates back to the sheet.

**PDF pipeline.**
Upload file → *PDF: Combine multiple PDF files into one* → *PDF: Compress* →
store the result in Google Drive.

---

## 9. Credits, rate limits & errors

- Each successful call consumes APIFreaks **credits** based on your plan. Track
  usage with the *General → Get credits usage information* module.
- Common responses:
  - **401 / authentication error** — the API key is missing or invalid; re‑check
    your connection.
  - **403 / plan error** — the endpoint isn't included in your current plan; see
    https://apifreaks.com/pricing.
  - **429 / too many requests** — you've hit the per‑minute rate limit; add a delay
    or reduce frequency.
- Live status: https://status.apifreaks.com

---

## 10. Tips

- Set the connection up once and reuse it everywhere.
- Use **bulk** modules when processing many inputs — fewer operations, faster runs.
- Map values between modules instead of hard‑coding them to build dynamic workflows.
- Start with **Run once** to inspect a module's output before wiring the rest of
  your scenario.

Questions or feature requests: support@apifreaks.com