# NYE in Sydney

An independent guide to Sydney New Year's Eve: a live countdown, an events directory with filters, fireworks vantage points, a planning guide, and a paid **List your event** page ($599).

## How it works

- `data/events.json`: every listing (name, venue, suburb, area, categories, price, inclusions, booking URL, `featured`).
- `src/style.css`, `src/main.js`: the design, the countdown, the fireworks animation, the directory filters and the listing form.
- `build.py`: generates the full static site into `docs/`.

```bash
python3 build.py                     # rebuild docs/
cd docs && python3 -m http.server    # preview at http://localhost:8000
```

`build.py` generates:

- Home page: countdown, filterable directory, timeline, vantage points and FAQ
- Category landing pages: dinners, cruises, parties and family
- Vantage points page
- Planning guide: times, transport, road closures and accessibility
- List-your-event page with the $599 offer and an intake form
- One SEO page per event, with `Event` schema
- `sitemap.xml`, `robots.txt`, `404.html` and the OG image

## Before going live: edit `CONFIG` in `build.py`

| Key | What to set |
| --- | --- |
| `site_url` | `https://nyeinsydney.com` (used for canonical URLs, the sitemap and OG tags) |
| `contact_email` | The inbox for listing requests |
| `form_endpoint` | A form backend URL (e.g. a Formspree form) that stores listing submissions |
| `payment_link` | A Stripe Payment Link for $599 AUD. After the form saves, the buyer is redirected here with their email prefilled |

Until `form_endpoint` is configured, the listing form opens the visitor's email app with their details filled in instead.

## Adding a paid listing

Add an entry to `data/events.json`. Set `"featured": true` if you want it pinned to the top with a badge. Then run `python3 build.py` and deploy.

## Deploying (Vercel)

`vercel.json` tells Vercel to serve the pre-built `docs/` folder. No build step runs, so always run `python3 build.py` and commit `docs/` before pushing.

1. On vercel.com, choose **Add New → Project**, import `adwordsmanagergc-wq/nyeinsydney` and click **Deploy**. No settings need changing.
2. Under **Project → Settings → Domains**, add `nyeinsydney.com` and `www.nyeinsydney.com`, then set the DNS records Vercel shows at your registrar (usually an A record `76.76.21.21` for the apex and a CNAME `cname.vercel-dns.com` for `www`). `vercel.json` already redirects `www` to the apex.
3. Every push to the production branch redeploys the site automatically.

After launch, submit `https://nyeinsydney.com/sitemap.xml` in Google Search Console.

To regenerate `og.png`, open `docs/og.html` at 1200×630 and screenshot it.
