# APIFreaks Make app - module index

**118 modules** (108 Action, 10 Search). `makeApiCall` is the universal catch-all.

## Commodity (5)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getCommodityFluctuation` | Action | GET | `/v1.0/commodity/fluctuation` |
| `getCommoditySymbols` | Action | GET | `/v1.0/commodity/symbols` |
| `getCommodityTimeSeries` | Action | GET | `/v1.0/commodity/time-series` |
| `getHistoricalCommodityPrices` | Action | GET | `/v1.0/commodity/rates/historical` |
| `getLatestCommodityPrices` | Action | GET | `/v1.0/commodity/rates/latest` |

## Currency (10)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `convertByIp` | Action | GET | `/v1.0/currency/converter/ip-to-currency` |
| `convertHistorical` | Action | GET | `/v1.0/currency/converter/historical/prices` |
| `convertLatest` | Action | GET | `/v1.0/currency/converter/latest/prices` |
| `getCurrencySymbols` | Action | GET | `/v1.0/currency/symbols` |
| `getFluctuation` | Action | GET | `/v1.0/currency/fluctuation` |
| `getHistoricalDataLimits` | Action | GET | `/v1.0/currency/historical/data/limits` |
| `getHistoricalExchangeRates` | Action | GET | `/v1.0/currency/rates/historical` |
| `getLatestExchangeRates` | Action | GET | `/v1.0/currency/rates/latest` |
| `getSupportedCurrencies` | Action | GET | `/v1.0/currency/supported` |
| `getTimeSeries` | Action | GET | `/v1.0/currency/time-series` |

## DNS (4)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `bulkDnsLookup` | Action | POST | `/v1.0/domain/dns/live` |
| `dnsHistoryLookup` | Action | GET | `/v1.0/domain/dns/history` |
| `dnsLookup` | Action | GET | `/v1.0/domain/dns/live` |
| `reverseDnsLookup` | Action | GET | `/v1.0/domain/dns/reverse` |

## Domain (4)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getDomainAvailability` | Action | GET | `/v1.0/domain/availability` |
| `getDomainAvailabilitySuggestions` | Action | GET | `/v1.0/domain/availability/suggestions` |
| `getSubdomainsLookup` | Action | GET | `/v1.0/subdomains/lookup` |
| `postDomainAvailability` | Action | POST | `/v1.0/domain/availability` |

## Email Validation (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `postEmailValidationBulk` | Action | POST | `/v1.0/email-validation/bulk` |
| `postEmailValidationSingle` | Action | POST | `/v1.0/email-validation/single` |

## Financial (8)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getIbanValidation` | Action | GET | `/v1.0/iban/validation` |
| `getSwiftCodeFinder` | Search | GET | `/v1.0/swift-code/finder` |
| `getSwiftCodeLookup` | Action | GET | `/v1.0/swift-code/lookup` |
| `getVatRatesCountry` | Search | GET | `/v1.0/vat/rates/country` |
| `getVatRatesIpAddress` | Search | GET | `/v1.0/vat/rates/ip-address` |
| `getVatSupportedCountries` | Action | GET | `/v1.0/vat/supported-countries` |
| `getVatValidation` | Action | GET | `/v1.0/vat/validation` |
| `postVatRatesCountry` | Action | POST | `/v1.0/vat/rates/country` |

## General (1)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getCreditsUsageInfo` | Action | GET | `/v1.0/credits/usage/info` |

## GeoDB (10)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getAdminUnits` | Action | GET | `/v1.0/geo/admin-levels` |
| `getCountries` | Action | GET | `/v1.0/geo/countries` |
| `getCountryDetails` | Action | GET | `/v1.0/geo/country/details` |
| `getFlags` | Action | GET | `/v1.0/flags` |
| `getFlagsSupported` | Search | GET | `/v1.0/flags/supported` |
| `getGeoAdminUnitDetails` | Action | GET | `/v1.0/geo/admin-unit/details` |
| `getGeoAdminUnits` | Action | GET | `/v1.0/geo/admin-units` |
| `getGeoCities` | Action | GET | `/v1.0/geo/cities` |
| `getGeoRegions` | Action | GET | `/v1.0/geo/regions` |
| `getSubregionsByRegion` | Action | GET | `/v1.0/geo/subregions` |

## Geocoding (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getGeocoderReverse` | Action | GET | `/v1.0/geocoder/reverse` |
| `getGeocoderSearch` | Search | GET | `/v1.0/geocoder/search` |

## IP Geolocation (6)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `bulkIpLookup` | Search | POST | `/v1.0/geolocation/lookup` |
| `bulkIpLookupV2` | Search | POST | `/v2.0/geolocation/lookup` |
| `bulkIpSecurityLookup` | Search | POST | `/v1.0/ip/security` |
| `getGeolocationLookup` | Action | GET | `/v1.0/geolocation/lookup` |
| `getGeolocationLookupV2` | Action | GET | `/v2.0/geolocation/lookup` |
| `getIpSecurity` | Action | GET | `/v1.0/ip/security` |

## OCR (1)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `ocrPredict` | Action | POST | `/v1.0/ocr/predict` |

## Other (3)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getGeolocationAstronomy` | Action | GET | `/v1.0/geolocation/astronomy` |
| `getGeolocationAstronomyV2` | Action | GET | `/v2.0/geolocation/astronomy` |
| `makeApiCall` | Action | {{parameters.method}} | `{{parameters.url}}` |

## PDF (23)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `deletePdfFile` | Action | DELETE | `/v1.0/pdf/file` |
| `getPdfFileStatus` | Action | GET | `/v1.0/pdf/file-status` |
| `getPdfFiles` | Action | GET | `/v1.0/pdf/files` |
| `getPdfResourceDownload` | Action | GET | `/v1.0/pdf/resource/download` |
| `getPdfTaskStatus` | Action | GET | `/v1.0/pdf/task-status` |
| `postPdfBmp` | Action | POST | `/v1.0/pdf/bmp` |
| `postPdfCompress` | Action | POST | `/v1.0/pdf/compress` |
| `postPdfDecrypt` | Action | POST | `/v1.0/pdf/decrypt` |
| `postPdfEncrypt` | Action | POST | `/v1.0/pdf/encrypt` |
| `postPdfExtractPages` | Action | POST | `/v1.0/pdf/extract-pages` |
| `postPdfGif` | Action | POST | `/v1.0/pdf/gif` |
| `postPdfJpg` | Action | POST | `/v1.0/pdf/jpg` |
| `postPdfLinearize` | Action | POST | `/v1.0/pdf/linearize` |
| `postPdfMerge` | Action | POST | `/v1.0/pdf/merge` |
| `postPdfPng` | Action | POST | `/v1.0/pdf/png` |
| `postPdfRemovePages` | Action | POST | `/v1.0/pdf/remove-pages` |
| `postPdfResourceUpload` | Action | POST | `/v1.0/pdf/resource/upload` |
| `postPdfResourceUploadBinary` | Action | POST | `/v1.0/pdf/resource/upload-binary` |
| `postPdfRestrict` | Action | POST | `/v1.0/pdf/restrict` |
| `postPdfRotate` | Action | POST | `/v1.0/pdf/rotate` |
| `postPdfSplit` | Action | POST | `/v1.0/pdf/split` |
| `postPdfTif` | Action | POST | `/v1.0/pdf/tif` |
| `postPdfUnrestrict` | Action | POST | `/v1.0/pdf/unrestrict` |

## Phone Validation (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `postPhoneValidation` | Action | POST | `/v1.0/phone/validation` |
| `postPhoneValidationBulk` | Search | POST | `/v1.0/phone/validation/bulk` |

## Readability (4)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `grammarCorrect` | Action | POST | `/v1.0/readability/grammar/correct` |
| `grammarDetect` | Action | POST | `/v1.0/readability/grammar/detect` |
| `readabilityScore` | Action | POST | `/v1.0/readability/score` |
| `weakWordsDetect` | Action | POST | `/v1.0/readability/weak-words` |

## SSL (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `sslCertificateChainLookup` | Action | GET | `/v1.0/domain/ssl/live/chain` |
| `sslCertificateLookup` | Action | GET | `/v1.0/domain/ssl/live` |

## Screenshot (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `bulkScreenshot` | Action | POST | `/v1.0/screenshot` |
| `websiteScreenshot` | Action | GET | `/v1.0/screenshot` |

## Timezone (3)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `convertTimezone` | Action | GET | `/v1.0/timezone/converter` |
| `getTimezone` | Action | GET | `/v1.0/geolocation/timezone` |
| `getTimezoneV2` | Action | GET | `/v2.0/geolocation/timezone` |

## User Agent (2)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getUserAgentLookup` | Action | GET | `/v1.0/user-agent/lookup` |
| `postUserAgentLookup` | Search | POST | `/v1.0/user-agent/lookup` |

## WHOIS (8)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getAsnWhoisLive` | Action | GET | `/v1.0/asn/whois/live` |
| `getDomainWhoisReverse` | Action | GET | `/v1.0/domain/whois/reverse` |
| `getIpWhoisLive` | Action | GET | `/v1.0/ip/whois/live` |
| `postDomainWhoisLive` | Action | POST | `/v1.0/domain/whois/live` |
| `postDomainWhoisLiveV2` | Action | POST | `/v2.0/domain/whois/live` |
| `whoisHistoryLookup` | Action | GET | `/v1.0/domain/whois/history` |
| `whoisLookup` | Action | GET | `/v1.0/domain/whois/live` |
| `whoisLookupV2` | Action | GET | `/v2.0/domain/whois/live` |

## Weather (8)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `getAirQuality` | Action | GET | `/v1.0/weather/air-quality` |
| `getCurrent` | Action | GET | `/v1.0/weather/current` |
| `getFlood` | Action | GET | `/v1.0/weather/flood` |
| `getForecast` | Action | GET | `/v1.0/weather/forecast` |
| `getHistorical` | Action | GET | `/v1.0/weather/historical` |
| `getMarine` | Action | GET | `/v1.0/weather/marine` |
| `getTimeSeries2` | Action | GET | `/v1.0/weather/time-series` |
| `postCurrent` | Action | POST | `/v1.0/weather/current` |

## Web Scraping (1)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `performScraping` | Action | POST | `/v1.0/scraping` |

## ZIP Code (7)

| module (name) | type | method | endpoint |
|---|---|---|---|
| `bulklookupZipCodesPost` | Action | POST | `/v1.0/zipcode/lookup` |
| `getZipcodeDistance` | Action | POST | `/v1.0/zipcode/distance` |
| `getZipcodeDistanceMatch` | Action | POST | `/v1.0/zipcode/distance/match` |
| `lookupZipCodes` | Action | GET | `/v1.0/zipcode/lookup` |
| `searchZipByCity` | Action | GET | `/v1.0/zipcode/search/city` |
| `searchZipByRadius` | Action | GET | `/v1.0/zipcode/search/radius` |
| `searchZipByRegion` | Action | GET | `/v1.0/zipcode/search/region` |
