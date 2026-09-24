# SEO implementation — 12 September 2026

## Applied in the website code

- Introduced descriptive French routes for all six services.
- Added permanent redirects from the legacy roofing-template service URLs.
- Introduced descriptive `/realisations/` and `/conseils/` routes for project and article pages.
- Added redirects for duplicate home, portfolio, contact and quote-form routes.
- Updated internal links and canonical URLs to use the new route structure.
- Corrected mismatched service titles, descriptions, Open Graph titles and Twitter titles.
- Replaced the six service hero images with local, crawlable `<img>` elements.
- Replaced homepage CSS-only service photos with responsive HTML images and meaningful French alt text.
- Added WebP responsive variants, explicit dimensions, lazy loading below the fold and high-priority hero loading.
- Added service image data to Open Graph, Twitter cards, Service schema and the XML image sitemap.
- Added the complete business street address and postal code to LocalBusiness schema.
- Removed placeholder social-profile URLs from `sameAs`; exact business profiles should be added when known.
- Removed the irrelevant Radiant template-vault upsell code from public pages.
- Added long-lived immutable caching for versioned image assets and basic security headers.
- Added `noindex,follow` to detected utility or duplicate pages.
- Regenerated the sitemap with canonical service, project and advice URLs plus important images.
- Added `scripts/seo_audit.py` to catch missing core metadata, headings, demo-domain links and non-crawlable service hero images.

## External actions still requiring the business owner

These cannot be completed safely from the static website repository:

- Verify the domain in Google Search Console and submit `/sitemap.xml`.
- Update the Google Business Profile with exact hours, service areas and categories.
- Provide the exact Facebook, Instagram, YouTube or LinkedIn profile URLs before restoring `sameAs`.
- Request and respond to genuine customer reviews; no testimonials were invented.
- Supply verified project locations, dates and customer details for richer case studies.
- Confirm opening hours and geographic coordinates before adding them to structured data.
- Configure production-host redirects and HTTPS headers to mirror `server.py` if deployment does not use this server.

## Ongoing content plan

- Publish one evidence-based project case study per completed installation.
- Publish useful advice addressing real customer questions about materials, maintenance, corrosion, planning and pricing.
- Add unique location content only where the company has genuine experience and supporting photographs.
- Review Search Console monthly for indexing issues, queries, click-through rate and Core Web Vitals.

## Multilingual (FR / EN / IT)

French pages at the repo root are the **source**. `/en/` and `/it/` are generated, fully translated static copies.

- Edit French pages or `assets/i18n/translations.js`, then run `python3 scripts/build_i18n.py` (add `--report` to list French text that still has no translation). Never edit files under `en/` or `it/` by hand.
- The build adds `hreflang` alternates, `og:locale`, self-referencing canonicals and a hidden `Langue` field on every form, and regenerates `sitemap.xml` with the three language versions of each page.
- The navbar language switcher (`assets/i18n/i18n.js`) is a set of real links to the same page in the other languages.
- Localised details: phone numbers use the international format in EN/IT, prices/dates follow each language's convention, and form phone/email fields get `inputmode`/`autocomplete` attributes.
