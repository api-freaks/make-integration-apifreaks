# APIFreaks Make app - module index

**118 modules** (101 Action, 17 Search), organised into 22 groups. `makeApiCall` is the universal catch-all.

V1 endpoints that have a V2 are kept and labelled *(legacy)*.

## IP Geolocation (6)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get IP geolocation (legacy) | `getGeolocationLookup` | Action | GET | `/v1.0/geolocation/lookup` |
| Bulk IP geolocation lookup (legacy) | `bulkIpLookup` | Search | POST | `/v1.0/geolocation/lookup` |
| Get IP security data | `getIpSecurity` | Action | GET | `/v1.0/ip/security` |
| Bulk IP security lookup | `bulkIpSecurityLookup` | Search | POST | `/v1.0/ip/security` |
| Get IP geolocation | `getGeolocationLookupV2` | Action | GET | `/v2.0/geolocation/lookup` |
| Bulk IP geolocation lookup | `bulkIpLookupV2` | Search | POST | `/v2.0/geolocation/lookup` |

## WHOIS (8)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get domain WHOIS (legacy) | `whoisLookup` | Action | GET | `/v1.0/domain/whois/live` |
| Bulk domain WHOIS (legacy) | `postDomainWhoisLive` | Action | POST | `/v1.0/domain/whois/live` |
| Get IP WHOIS | `getIpWhoisLive` | Action | GET | `/v1.0/ip/whois/live` |
| Get ASN WHOIS | `getAsnWhoisLive` | Action | GET | `/v1.0/asn/whois/live` |
| Get domain WHOIS history | `whoisHistoryLookup` | Action | GET | `/v1.0/domain/whois/history` |
| Search reverse domain WHOIS | `getDomainWhoisReverse` | Search | GET | `/v1.0/domain/whois/reverse` |
| Get domain WHOIS | `whoisLookupV2` | Action | GET | `/v2.0/domain/whois/live` |
| Bulk domain WHOIS | `postDomainWhoisLiveV2` | Action | POST | `/v2.0/domain/whois/live` |

## DNS (4)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get DNS records | `dnsLookup` | Action | GET | `/v1.0/domain/dns/live` |
| Bulk DNS lookup | `bulkDnsLookup` | Action | POST | `/v1.0/domain/dns/live` |
| Search DNS history | `dnsHistoryLookup` | Search | GET | `/v1.0/domain/dns/history` |
| Search reverse DNS records | `reverseDnsLookup` | Search | GET | `/v1.0/domain/dns/reverse` |

## Domain (4)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Check domain availability | `getDomainAvailability` | Action | GET | `/v1.0/domain/availability` |
| Check domain availability in bulk | `postDomainAvailability` | Action | POST | `/v1.0/domain/availability` |
| Suggest available domains | `getDomainAvailabilitySuggestions` | Action | GET | `/v1.0/domain/availability/suggestions` |
| Search subdomains | `getSubdomainsLookup` | Search | GET | `/v1.0/subdomains/lookup` |

## SSL (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get SSL certificate | `sslCertificateLookup` | Action | GET | `/v1.0/domain/ssl/live` |
| Get SSL certificate chain | `sslCertificateChainLookup` | Action | GET | `/v1.0/domain/ssl/live/chain` |

## Geocoding (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Search addresses (forward geocoding) | `getGeocoderSearch` | Search | GET | `/v1.0/geocoder/search` |
| Reverse geocode coordinates | `getGeocoderReverse` | Action | GET | `/v1.0/geocoder/reverse` |

## GeoDB (10)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| List countries | `getCountries` | Action | GET | `/v1.0/geo/countries` |
| Get country details | `getCountryDetails` | Action | GET | `/v1.0/geo/country/details` |
| List regions | `getGeoRegions` | Action | GET | `/v1.0/geo/regions` |
| List subregions by region | `getSubregionsByRegion` | Action | GET | `/v1.0/geo/subregions` |
| List administrative levels | `getAdminUnits` | Action | GET | `/v1.0/geo/admin-levels` |
| List administrative units | `getGeoAdminUnits` | Action | GET | `/v1.0/geo/admin-units` |
| Get administrative unit details | `getGeoAdminUnitDetails` | Action | GET | `/v1.0/geo/admin-unit/details` |
| List cities | `getGeoCities` | Action | GET | `/v1.0/geo/cities` |
| List supported flags | `getFlagsSupported` | Search | GET | `/v1.0/flags/supported` |
| Get country flags | `getFlags` | Action | GET | `/v1.0/flags` |

## ZIP Code (7)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Look up ZIP codes | `lookupZipCodes` | Action | GET | `/v1.0/zipcode/lookup` |
| Look up ZIP codes in bulk | `bulklookupZipCodesPost` | Action | POST | `/v1.0/zipcode/lookup` |
| Search ZIP by city | `searchZipByCity` | Search | GET | `/v1.0/zipcode/search/city` |
| Search ZIP by region | `searchZipByRegion` | Search | GET | `/v1.0/zipcode/search/region` |
| Search ZIP by radius | `searchZipByRadius` | Search | GET | `/v1.0/zipcode/search/radius` |
| Get distance between ZIP codes | `getZipcodeDistance` | Action | POST | `/v1.0/zipcode/distance` |
| Match ZIP codes by distance | `getZipcodeDistanceMatch` | Action | POST | `/v1.0/zipcode/distance/match` |

## Currency (10)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get latest exchange rates | `getLatestExchangeRates` | Action | GET | `/v1.0/currency/rates/latest` |
| Get historical exchange rates | `getHistoricalExchangeRates` | Action | GET | `/v1.0/currency/rates/historical` |
| Convert currency (latest) | `convertLatest` | Action | GET | `/v1.0/currency/converter/latest/prices` |
| Convert currency (historical) | `convertHistorical` | Action | GET | `/v1.0/currency/converter/historical/prices` |
| Get currency time series | `getTimeSeries` | Action | GET | `/v1.0/currency/time-series` |
| Get currency fluctuation | `getFluctuation` | Action | GET | `/v1.0/currency/fluctuation` |
| Convert currency by IP | `convertByIp` | Action | GET | `/v1.0/currency/converter/ip-to-currency` |
| List supported currencies | `getSupportedCurrencies` | Action | GET | `/v1.0/currency/supported` |
| List currency symbols | `getCurrencySymbols` | Action | GET | `/v1.0/currency/symbols` |
| Get historical data limits | `getHistoricalDataLimits` | Action | GET | `/v1.0/currency/historical/data/limits` |

## Commodity (5)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get latest commodity prices | `getLatestCommodityPrices` | Action | GET | `/v1.0/commodity/rates/latest` |
| Get historical commodity prices | `getHistoricalCommodityPrices` | Action | GET | `/v1.0/commodity/rates/historical` |
| Get commodity time series | `getCommodityTimeSeries` | Action | GET | `/v1.0/commodity/time-series` |
| Get commodity fluctuation | `getCommodityFluctuation` | Action | GET | `/v1.0/commodity/fluctuation` |
| List commodity symbols | `getCommoditySymbols` | Action | GET | `/v1.0/commodity/symbols` |

## Financial (8)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| List VAT-supported countries | `getVatSupportedCountries` | Action | GET | `/v1.0/vat/supported-countries` |
| Search VAT rates by IP address | `getVatRatesIpAddress` | Search | GET | `/v1.0/vat/rates/ip-address` |
| Search VAT rates by country | `getVatRatesCountry` | Search | GET | `/v1.0/vat/rates/country` |
| Get VAT rates for countries | `postVatRatesCountry` | Action | POST | `/v1.0/vat/rates/country` |
| Validate a VAT number | `getVatValidation` | Action | GET | `/v1.0/vat/validation` |
| Validate an IBAN | `getIbanValidation` | Action | GET | `/v1.0/iban/validation` |
| Search SWIFT codes | `getSwiftCodeFinder` | Search | GET | `/v1.0/swift-code/finder` |
| Get SWIFT code details | `getSwiftCodeLookup` | Action | GET | `/v1.0/swift-code/lookup` |

## Weather (8)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get current weather | `getCurrent` | Action | GET | `/v1.0/weather/current` |
| Get current weather in bulk | `postCurrent` | Action | POST | `/v1.0/weather/current` |
| Get weather forecast | `getForecast` | Action | GET | `/v1.0/weather/forecast` |
| Get historical weather | `getHistorical` | Action | GET | `/v1.0/weather/historical` |
| Get weather time series | `getWeatherTimeSeries` | Action | GET | `/v1.0/weather/time-series` |
| Get marine weather | `getMarine` | Action | GET | `/v1.0/weather/marine` |
| Get air quality | `getAirQuality` | Action | GET | `/v1.0/weather/air-quality` |
| Get flood data | `getFlood` | Action | GET | `/v1.0/weather/flood` |

## Timezone (3)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get timezone by IP (legacy) | `getTimezone` | Action | GET | `/v1.0/geolocation/timezone` |
| Convert time between timezones | `convertTimezone` | Action | GET | `/v1.0/timezone/converter` |
| Get timezone by IP | `getTimezoneV2` | Action | GET | `/v2.0/geolocation/timezone` |

## Astronomy (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get astronomy data (legacy) | `getGeolocationAstronomy` | Action | GET | `/v1.0/geolocation/astronomy` |
| Get astronomy data | `getGeolocationAstronomyV2` | Action | GET | `/v2.0/geolocation/astronomy` |

## Email & Phone Validation (4)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Validate an email address | `postEmailValidationSingle` | Action | POST | `/v1.0/email-validation/single` |
| Validate emails in bulk | `postEmailValidationBulk` | Action | POST | `/v1.0/email-validation/bulk` |
| Validate a phone number | `postPhoneValidation` | Action | POST | `/v1.0/phone/validation` |
| Search validated phone numbers | `postPhoneValidationBulk` | Search | POST | `/v1.0/phone/validation/bulk` |

## User Agent (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Look up a user agent | `getUserAgentLookup` | Action | GET | `/v1.0/user-agent/lookup` |
| Look up user agents in bulk | `postUserAgentLookup` | Search | POST | `/v1.0/user-agent/lookup` |

## Readability (4)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Detect grammar errors | `grammarDetect` | Action | POST | `/v1.0/readability/grammar/detect` |
| Correct grammar | `grammarCorrect` | Action | POST | `/v1.0/readability/grammar/correct` |
| Detect weak words | `weakWordsDetect` | Action | POST | `/v1.0/readability/weak-words` |
| Score readability | `readabilityScore` | Action | POST | `/v1.0/readability/score` |

## OCR (1)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Extract text with OCR | `ocrPredict` | Action | POST | `/v1.0/ocr/predict` |

## Web Scraping (1)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Scrape a web page | `performScraping` | Action | POST | `/v1.0/scraping` |

## Screenshot (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Capture a website screenshot | `websiteScreenshot` | Action | GET | `/v1.0/screenshot` |
| Capture website screenshots in bulk | `bulkScreenshot` | Action | POST | `/v1.0/screenshot` |

## PDF (23)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Merge PDF files | `postPdfMerge` | Action | POST | `/v1.0/pdf/merge` |
| Remove PDF pages | `postPdfRemovePages` | Action | POST | `/v1.0/pdf/remove-pages` |
| Split a PDF | `postPdfSplit` | Action | POST | `/v1.0/pdf/split` |
| Rotate PDF pages | `postPdfRotate` | Action | POST | `/v1.0/pdf/rotate` |
| Compress a PDF | `postPdfCompress` | Action | POST | `/v1.0/pdf/compress` |
| Extract PDF pages | `postPdfExtractPages` | Action | POST | `/v1.0/pdf/extract-pages` |
| Linearize a PDF | `postPdfLinearize` | Action | POST | `/v1.0/pdf/linearize` |
| Encrypt a PDF | `postPdfEncrypt` | Action | POST | `/v1.0/pdf/encrypt` |
| Decrypt a PDF | `postPdfDecrypt` | Action | POST | `/v1.0/pdf/decrypt` |
| Restrict a PDF | `postPdfRestrict` | Action | POST | `/v1.0/pdf/restrict` |
| Remove PDF restrictions | `postPdfUnrestrict` | Action | POST | `/v1.0/pdf/unrestrict` |
| Convert a PDF to PNG | `postPdfPng` | Action | POST | `/v1.0/pdf/png` |
| Convert a PDF to JPG | `postPdfJpg` | Action | POST | `/v1.0/pdf/jpg` |
| Convert a PDF to TIFF | `postPdfTif` | Action | POST | `/v1.0/pdf/tif` |
| Convert a PDF to BMP | `postPdfBmp` | Action | POST | `/v1.0/pdf/bmp` |
| Convert a PDF to GIF | `postPdfGif` | Action | POST | `/v1.0/pdf/gif` |
| Upload PDF files | `postPdfResourceUpload` | Action | POST | `/v1.0/pdf/resource/upload` |
| Upload a PDF (binary) | `postPdfResourceUploadBinary` | Action | POST | `/v1.0/pdf/resource/upload-binary` |
| Download a processed file | `getPdfResourceDownload` | Action | GET | `/v1.0/pdf/resource/download` |
| Get PDF task status | `getPdfTaskStatus` | Action | GET | `/v1.0/pdf/task-status` |
| Get PDF file status | `getPdfFileStatus` | Action | GET | `/v1.0/pdf/file-status` |
| List uploaded PDF files | `getPdfFiles` | Action | GET | `/v1.0/pdf/files` |
| Delete an uploaded PDF file | `deletePdfFile` | Action | DELETE | `/v1.0/pdf/file` |

## General (2)

| label | module (name) | type | method | endpoint |
|---|---|---|---|---|
| Get credits usage information | `getCreditsUsageInfo` | Action | GET | `/v1.0/credits/usage/info` |
| Make an API Call | `makeApiCall` | Action | * | `{url}` |

