#!/usr/bin/env python3
"""Static site generator for NYE in Sydney.

Edit data/events.json (and the CONFIG block below), then run:
    python3 build.py
The complete site is written to ./docs, which Vercel serves as-is (see vercel.json).
"""
import hashlib
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

# --------------------------------------------------------------------------------------
# CONFIG: change these before going live
# --------------------------------------------------------------------------------------
CONFIG = {
    "site_name": "NYE in Sydney",
    "site_url": "https://nyeinsydney.com",   # your live domain, no trailing slash
    "contact_email": "aj@metatapdigital.com",
    "listing_price": 599,                     # AUD, inc GST
    # Listing submissions are emailed to contact_email via FormSubmit (no account needed;
    # the first submission sends a one-time activation email to that inbox).
    "form_endpoint": "https://formsubmit.co/ajax/aj@metatapdigital.com",
    # Stripe Payment Link (or similar) for the $599 listing fee. While it still contains
    # "YOUR_", submitters see a thank-you message and you email them an invoice instead.
    "payment_link": "https://buy.stripe.com/YOUR_PAYMENT_LINK",
    "year": 2026,
    "next_year": 2027,
}

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
EVENTS = json.loads((ROOT / "data" / "events.json").read_text())
TODAY = date.today().isoformat()
Y, NY = CONFIG["year"], CONFIG["next_year"]
URL = CONFIG["site_url"]
P = CONFIG["listing_price"]
# Content hashes for cache busting: the CSS/JS URLs change whenever the files do.
VER = {f: hashlib.md5((ROOT / "src" / f).read_bytes()).hexdigest()[:10] for f in ("style.css", "main.js")}

CATEGORY_LABELS = {
    "party": "Parties",
    "dining": "Dinners",
    "fine-dining": "Fine dining",
    "cruise": "Cruises",
    "rooftop": "Rooftops",
    "harbour": "Harbourfront",
    "family": "Family-friendly",
    "budget": "Under $250",
    "vantage": "Ticketed vantage points",
    "free": "Free",
    "beach": "Beach",
}
AREAS = sorted({e["area"] for e in EVENTS})

NAV = [
    ("/#directory", "Events"),
    ("/new-years-eve-dinner-sydney/", "Dinners"),
    ("/new-years-eve-cruises-sydney/", "Cruises"),
    ("/new-years-eve-parties-sydney/", "Parties"),
    ("/sydney-fireworks-vantage-points/", "Vantage points"),
    ("/plan-your-night/", "Plan"),
]

# Photography: Wikimedia Commons, freely licensed. Resized to WebP in src/img.
PHOTOS = {
    "fleet": {
        "file": "fleet-steps-2023", "w": 1920, "h": 1260,
        "alt": "Midnight fireworks and smoke over Sydney Harbour, with the Opera House lit up and boats on the water",
        "credit": "Dicklyon", "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Sydney_Harbour_fireworks_and_smoke_2023.jpg",
    },
    "reflections": {
        "file": "harbour-reflections-2025", "w": 1920, "h": 1457,
        "alt": "Fireworks over the Harbour Bridge reflected in the water, with cruise boats on the harbour",
        "credit": "Dicklyon", "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Sydney_welcomes_2025.jpg",
    },
    "bridge": {
        "file": "bridge-opera-house-2008", "w": 1920, "h": 1190,
        "alt": "A crowd watching gold fireworks over the Sydney Harbour Bridge and Opera House",
        "credit": "Linh_rOm", "license": "CC BY 2.0", "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Sydney_habour_bridge_%26_opera_house_fireworks_new_year_eve_2008.jpg",
    },
    "red": {
        "file": "harbour-bridge-2014", "w": 1920, "h": 1539,
        "alt": "Red fireworks over the Harbour Bridge reflected across the water",
        "credit": "Ian Rose", "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "source": "https://commons.wikimedia.org/wiki/File:NYE2014_-_Sydney_Harbour.JPG",
    },
}
CAT_PHOTO = {"cruise": "reflections", "dining": "bridge", "fine-dining": "bridge", "party": "red", "vantage": "fleet"}


def j(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")


def money(n):
    return "Free" if n == 0 else f"${n:,.0f}"


def icon(name):
    return f'<i class="ph ph-{name}" aria-hidden="true"></i>'


ARROW = icon("arrow-right")


def img(key, cls="", sizes="100vw", eager=False):
    p = PHOTOS[key]
    f = p["file"]
    load = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img class="{cls}" src="/img/{f}-1920.webp" srcset="/img/{f}-960.webp 960w, /img/{f}-1920.webp 1920w" '
            f'sizes="{sizes}" width="{p["w"]}" height="{p["h"]}" alt="{escape(p["alt"])}" {load}>')


def words(text, accent=None, start=0):
    """Wrap each word for the staggered headline reveal. `accent` words get the gold colour."""
    out, i = [], start
    for w in text.split():
        cls = ' class="accent"' if accent and w in accent else ""
        out.append(f'<span class="w"><span{cls} style="--i:{i}">{escape(w)}</span></span>')
        i += 1
    return " ".join(out)


def countdown(size="lg", label=None):
    units = [("d", "days"), ("h", "hrs"), ("m", "min"), ("s", "sec")]
    inner = "".join(
        f'<div class="cd-u"><span class="cd-n" data-u="{k}">00</span><span class="cd-l">{v}</span></div>'
        for k, v in units
    )
    lab = f'<p class="cd-cap">{label}</p>' if label else ""
    return (f'<div class="cd cd--{size}"><div class="cd-row" data-countdown role="timer" '
            f'aria-label="Countdown to midnight, New Year\'s Eve {Y} in Sydney">{inner}</div>{lab}</div>')


def deadline():
    return f'<p class="cd-deadline">{icon("clock")} Midnight AEDT, Thursday 31 December {Y}</p>'


# --------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------
def layout(path, title, description, body, schema=None, og_type="website", active=None, head_extra="", og_image=None):
    canonical = URL + path
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": CONFIG["site_name"],
            "url": URL + "/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": URL + "/?q={search_term_string}#directory",
                "query-input": "required name=search_term_string",
            },
        }
    ] if path == "/" else []
    schemas += schema or []
    cur = ' aria-current="page"'
    nav = "".join(f'<li><a href="{h}"{cur if h == (active or path) else ""}>{t}</a></li>' for h, t in NAV)
    ld = "".join(f'<script type="application/ld+json">{j(s)}</script>' for s in schemas)
    og = og_image or f"{URL}/og.jpg"
    credits = " ".join(
        f'<a href="{p["source"]}" rel="noopener" target="_blank">Photo: {escape(p["credit"])}</a> '
        f'(<a href="{p["license_url"]}" rel="noopener license" target="_blank">{p["license"]}</a>), resized.'
        for p in PHOTOS.values()
    )
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="AU-NSW"><meta name="geo.placename" content="Sydney">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{CONFIG['site_name']}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{og}"><meta property="og:locale" content="en_AU">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#080a10">
<script>document.documentElement.classList.add("js")</script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Geist:wght@400..600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">
{head_extra}
<link rel="stylesheet" href="/style.css?v={VER['style.css']}">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav" data-nav><div class="wrap nav-in">
<a class="logo" href="/" aria-label="NYE in Sydney, home">NYE <span>in</span> Sydney</a>
<nav aria-label="Main"><ul id="menu">{nav}</ul></nav>
<a class="btn btn-gold btn-sm nav-cta" href="/list-your-event/">List your event</a>
<button class="menu-btn" aria-label="Open menu" aria-expanded="false" aria-controls="menu">{icon("list")}</button>
</div></header>
<main id="main">
<div class="nav-sentinel" aria-hidden="true"></div>
{body}
</main>
<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div class="foot-brand"><a class="logo" href="/">NYE <span>in</span> Sydney</a>
<p>The independent guide to New Year's Eve {Y} in Sydney: vantage points, harbour cruises, dinners and parties in one place.</p>
{countdown("sm")}</div>
<div><h2 class="foot-h">Explore</h2><ul>
<li><a href="/#directory">All NYE events</a></li><li><a href="/new-years-eve-dinner-sydney/">NYE dinners</a></li>
<li><a href="/new-years-eve-cruises-sydney/">NYE cruises</a></li><li><a href="/new-years-eve-parties-sydney/">NYE parties</a></li>
<li><a href="/family-new-years-eve-sydney/">Family NYE</a></li></ul></div>
<div><h2 class="foot-h">Plan</h2><ul>
<li><a href="/sydney-fireworks-vantage-points/">Vantage points map</a></li><li><a href="/plan-your-night/">Fireworks times</a></li>
<li><a href="/plan-your-night/#transport">Transport</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
<div><h2 class="foot-h">Venues</h2><ul>
<li><a href="/list-your-event/">List your event, ${P}</a></li>
<li><a href="/about/">About NYE in Sydney</a></li>
<li><a href="mailto:{CONFIG['contact_email']}">{CONFIG['contact_email']}</a></li></ul></div>
</div>
<p class="fine">NYE in Sydney is an independent guide and is not affiliated with the City of Sydney or the official Sydney New Year's Eve event. Prices and details come from venues or their published information and can change, so confirm with the venue before booking. We acknowledge the Gadigal of the Eora Nation, the Traditional Custodians of the land and waters of Sydney Harbour. © {Y} {CONFIG['site_name']}.</p>
<p class="fine credits">Photography via Wikimedia Commons. {credits}</p>
</div></footer>
<div class="grain" aria-hidden="true"></div>
<script src="/main.js?v={VER['main.js']}" defer></script>
</body>
</html>"""


def hero(photo, h1, sub, ctas, aside="", kind="full", crumbs="", pos="center"):
    return f"""<section class="hero hero--{kind}" data-hero style="--pos:{pos}">
<div class="hero-media">{img(photo, "hero-img", eager=True)}</div>
<canvas class="fx" data-fireworks aria-hidden="true"></canvas>
<div class="hero-shade" aria-hidden="true"></div>
<div class="wrap hero-grid">
<div class="hero-copy">{crumbs}<h1>{h1}</h1><p class="hero-sub reveal" style="--i:6">{sub}</p>
<div class="hero-ctas reveal" style="--i:7">{ctas}</div></div>
{f'<div class="hero-aside reveal" style="--i:8">{aside}</div>' if aside else ''}
</div></section>"""


# --------------------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------------------
def card(e, i):
    cats = " ".join(e["categories"])
    search = " ".join([e["name"], e["venue"], e["suburb"], e["area"], " ".join(e["categories"]), e["blurb"]]).lower()
    tags = "".join(f"<li>{CATEGORY_LABELS.get(c, c)}</li>" for c in e["categories"][:2])
    price = e["price_from"]
    price_html = (
        "<b>Free</b><span>ticket required</span>" if price == 0
        else f"<b>{money(price)}</b><span>from, per person</span>" if price
        else "<b>TBA</b><span>see venue</span>"
    )
    loc = e["suburb"] if e["suburb"] in e["area"] else f'{e["suburb"]}, {e["area"]}'
    return f"""<article class="ev reveal{' is-feat' if e.get('featured') else ''}" style="--i:{i % 6};view-transition-name:ev-{e['slug']}" data-cats="{cats}" data-area="{escape(e['area'])}" data-price="{price if price is not None else ''}" data-featured="{1 if e.get('featured') else 0}" data-order="{i}" data-search="{escape(search)}">
<div class="ev-top"><span class="ev-loc">{icon("map-pin")} {escape(loc)}</span>{'<span class="ev-feat">Featured</span>' if e.get('featured') else ''}</div>
<h3><a class="ev-link" href="/events/{e['slug']}/">{escape(e['name'])}</a></h3>
<p>{escape(e['blurb'])}</p>
<ul class="ev-tags"><li class="ev-fw">{icon("sparkle")} {escape(e['fireworks'])}</li>{tags}</ul>
<div class="ev-foot"><div class="ev-price">{price_html}</div>
<a class="btn btn-gold btn-sm ev-book" href="{e['url']}" target="_blank" rel="noopener sponsored">Book {icon("arrow-up-right")}</a></div>
</article>"""


def directory(events, heading, sub, show_filters=True, anchor="directory"):
    used = []
    for e in events:
        for c in e["categories"]:
            if c not in used:
                used.append(c)
    order = [c for c in CATEGORY_LABELS if c in used]
    chips = '<button class="chip" data-cat="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" data-cat="{c}" aria-pressed="false">{CATEGORY_LABELS[c]}</button>' for c in order
    )
    areas = '<option value="all">All areas</option>' + "".join(
        f'<option>{escape(a)}</option>' for a in AREAS if any(e["area"] == a for e in events)
    )
    filters = f"""<div class="dir-tools">
<label class="search">{icon("magnifying-glass")}<span class="sr">Search events</span><input id="q" type="search" placeholder="Search venue, suburb or vibe" autocomplete="off"></label>
<label class="sel"><span class="sr">Filter by area</span><select id="area">{areas}</select>{icon("caret-down")}</label>
<label class="sel"><span class="sr">Sort</span><select id="sort"><option value="featured">Featured first</option><option value="low">Price, low to high</option><option value="high">Price, high to low</option></select>{icon("caret-down")}</label>
</div>
<div class="chips" role="group" aria-label="Filter by type">{chips}</div>
<p class="count" aria-live="polite"></p>""" if show_filters else ""
    cards = "".join(card(e, i) for i, e in enumerate(events))
    return f"""<section class="sec" id="{anchor}" data-directory><div class="wrap">
<div class="sec-head split"><h2 class="reveal">{heading}</h2><p class="reveal" style="--i:1">{sub}</p></div>
{filters}
<div class="ev-grid">{cards}</div>
<p class="empty">No events match that search. Try another filter, or <a href="/list-your-event/">list yours</a>.</p>
</div></section>"""


def list_band():
    return f"""<section class="sec sec--tight"><div class="wrap"><div class="band reveal">
<div><h2>Selling NYE tickets in Sydney?</h2><p>October to December is when Sydney searches for New Year's Eve plans. Be in front of them for ${P}, no commission.</p></div>
<a class="btn btn-ink" href="/list-your-event/">List your event {ARROW}</a></div></div></section>"""


def item_list(events, name):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(events),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{URL}/events/{e['slug']}/", "name": e["name"]}
            for i, e in enumerate(events)
        ],
    }


def breadcrumbs(*pairs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": URL + p} for i, (n, p) in enumerate(pairs)
        ],
    }


def crumb_html(*pairs):
    parts = [f'<a href="{p}">{escape(n)}</a>' for n, p in pairs[:-1]] + [f'<span aria-current="page">{escape(pairs[-1][0])}</span>']
    return f'<nav class="crumbs reveal" aria-label="Breadcrumb">{" / ".join(parts)}</nav>'


# --------------------------------------------------------------------------------------
# Content: FAQ, timeline, vantage points
# --------------------------------------------------------------------------------------
FAQ = [
    (f"What time are the Sydney New Year's Eve fireworks in {Y}?",
     f"There are two main displays on Thursday 31 December {Y}. The 9pm Family Fireworks run for about 8 to 10 minutes and are made for kids and early nights. The Midnight Fireworks, the main show seen around the world, run for about 12 minutes and launch from the Sydney Harbour Bridge, barges and city rooftops to welcome {NY}."),
    ("Where is the best place to watch the Sydney fireworks?",
     "For the classic Opera House and Harbour Bridge view, try Mrs Macquaries Point, Blues Point Reserve, Lower Bradfield Park, Hickson Road Reserve or the Opera House forecourt. If you want a guaranteed spot without camping out from the morning, book a ticketed vantage point (from about $65), a harbourside dinner or party, or a fireworks cruise."),
    ("Are the Sydney NYE fireworks free to watch?",
     "Yes. Many harbour foreshore vantage points are free and open on a first-come, first-served basis. Some places need a free ticket (for example the Opera House forecourt and some islands), and some are paid ticketed areas run by councils with guaranteed entry, food and toilets."),
    ("How much does a New Year's Eve cruise on Sydney Harbour cost?",
     "All-inclusive party boats start from about $700 per person, and dinner cruises and small luxury yachts run up to about $2,500. Short 9pm family cruises start from about $265 for kids and $425 for adults. Packages normally include a multi-course meal or canapés, drinks and a DJ or entertainment. Smaller boats and early-release tickets tend to sell out first."),
    ("Where can I have dinner with a fireworks view in Sydney?",
     "Harbourfront restaurants like Bennelong, Whalebridge, Altitude at the Shangri-La, The Fenwick, Sails on Lavender Bay and Jounieh at Dawes Point all run NYE menus with fireworks views. Early sittings, such as Jounieh's 9pm seating from $260, cost far less than late sittings. See our <a href=\"/new-years-eve-dinner-sydney/\">NYE dinners in Sydney</a> list."),
    ("What time should I arrive at a free vantage point?",
     "The most popular foreshore spots, such as Mrs Macquaries Point and Hickson Road, can reach capacity by mid-morning on 31 December. Lesser-known parks in Balmain, Birchgrove and the North Shore usually fill by mid-to-late afternoon. Once a site is full, entry closes."),
    ("Is there public transport on New Year's Eve in Sydney?",
     "Yes. Extra trains, buses and ferries run all evening and through the night, and many city roads close from the afternoon. Public transport is by far the easiest way in and out. Check transportnsw.info for the official NYE timetable and road closures closer to the date."),
    ("Can I bring alcohol to the Sydney fireworks?",
     "It depends on the location. Many foreshore vantage points are alcohol-free zones, some allow BYO, and others have licensed bars. Check the rules for your chosen spot before you go. Glass is usually banned at public vantage points."),
    ("What are the best family-friendly NYE options in Sydney?",
     "The 9pm Family Fireworks are made for kids. Family-friendly options include ticketed parks like Lower Bradfield Park, Blues Point and Dudley Page Reserve, Taronga Zoo's picnic lawn tiers, Fantasea's 9pm family cruise, early dinner sittings, and quieter harbourside parks in Balmain and the North Shore."),
    ("Is NYE in Sydney the official Sydney New Year's Eve website?",
     "No. NYE in Sydney is an independent guide and event directory. The official event is produced by the City of Sydney. We bring together official vantage-point information and bookable dinners, cruises and parties so you can plan the whole night in one place."),
    ("How do I list my New Year's Eve event on NYE in Sydney?",
     f"It's a one-off ${P} fee with no commission. Your event gets its own optimised page, a place in our directory and category pages, and a direct link to your booking page. <a href=\"/list-your-event/\">List your event here</a>."),
]


def faq_block(items, heading, sub):
    qs = "".join(
        f'<details class="reveal" style="--i:{i % 6}"><summary>{escape(q)}{icon("plus")}</summary><div class="ans"><p>{a}</p></div></details>'
        for i, (q, a) in enumerate(items)
    )
    return f"""<section class="sec" id="faq"><div class="wrap faq-grid">
<div class="faq-side"><h2 class="reveal">{heading}</h2><p class="reveal" style="--i:1">{sub}</p></div>
<div class="faq">{qs}</div></div></section>"""


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
        ],
    }


# (label, description, sky 0 day / 1 dusk / 2 night / 3 midnight, burst: "", "family", "midnight")
TIMELINE = [
    ("Morning", "Free foreshore vantage points open. The most popular spots can fill by mid-morning.", 0, ""),
    ("Afternoon", "Road closures start around the CBD and harbour. Ticketed parks and venues open their gates.", 0, ""),
    ("Early evening", "Aerial displays and on-water entertainment begin across the harbour.", 1, ""),
    ("8:30pm", "Calling Country and Welcome to Country ceremonies honour the Traditional Custodians of the harbour.", 1, ""),
    ("9:00pm", "The Family Fireworks. Around 8 to 10 minutes, made for kids and early nights.", 2, "family"),
    ("9:15pm", "The Harbour of Light Parade: illuminated vessels sail the harbour.", 2, ""),
    ("Midnight", f"The Midnight Fireworks. Around 12 minutes off the Harbour Bridge, barges and rooftops to welcome {NY}.", 3, "midnight"),
    ("After midnight", "Extra trains, buses and ferries run all night to get the crowds home. Allow plenty of time.", 2, ""),
]


def night_story(heading, sub):
    steps = "".join(
        f'<li class="step" data-step data-sky="{sky}" data-burst="{burst}" data-clock="{escape(t)}"><h3>{escape(t)}</h3><p>{escape(d)}</p></li>'
        for t, d, sky, burst in TIMELINE
    )
    return f"""<section class="sec night" id="night"><div class="wrap">
<div class="sec-head split"><h2 class="reveal">{heading}</h2><p class="reveal" style="--i:1">{sub}</p></div>
<div class="night-grid">
<div class="stage" aria-hidden="true">
<div class="sky sky-0"></div><div class="sky sky-1"></div><div class="sky sky-2"></div><div class="sky sky-3"></div>
<canvas class="fx" data-fireworks="story"></canvas>
<div class="stage-clock" data-stage-clock>Morning</div>
<div class="stage-water"></div>
</div>
<ol class="steps">{steps}</ol>
</div></div></section>"""


# name, area, view, entry type, note, lat, lng
VANTAGE = [
    ("Mrs Macquaries Point", "Royal Botanic Garden", "Opera House and Bridge together", "free", "The postcard view, and one of the first spots to fill", -33.8597, 151.2226),
    ("Hickson Road Reserve", "The Rocks", "Right under the Bridge", "free", "Alcohol-free and fills very early", -33.8553, 151.2089),
    ("Sydney Opera House Forecourt", "Bennelong Point", "Front row to the harbour", "free-t", "Free ticket released 10am, 26 December. Bars on site", -33.8575, 151.2148),
    ("Bennelong Lawn, Fleet Steps and Tarpeian Lawn", "Royal Botanic Garden", "Opera House and Bridge", "check", "Food and drink available. Check entry conditions", -33.8592, 151.2172),
    ("Lower Bradfield Park", "Milsons Point", "Directly beside the Bridge", "paid", "$65 ticketed, guaranteed entry and facilities", -33.8476, 151.2117),
    ("Blues Point Reserve", "McMahons Point", "Bridge and Opera House lined up", "paid", "$65 ticketed, guaranteed entry", -33.8468, 151.2032),
    ("Cremorne Point and Lavender Bay", "North Shore", "Harbour and city skyline", "check", "Managed by North Sydney Council", -33.8443, 151.2295),
    ("Dudley Page Reserve", "Dover Heights", "Elevated panorama of the skyline", "paid", "$70 adult, $30 youth, $180 family", -33.8770, 151.2800),
    ("Bradleys Head", "Mosman", "Headland facing the city", "free-t", "Free ticket (booked out). Alcohol and glass free", -33.8538, 151.2462),
    ("Strickland Estate", "Vaucluse", "Harbour lawns with Bridge views", "free-t", "Free ticket (booked out); general entry may open from 6pm", -33.8519, 151.2667),
    ("Goat Island", "On the harbour", "Island close to the Bridge", "free-t", "Free ticket plus ferry pass", -33.8523, 151.1960),
    ("Clark Island and Shark Island", "On the harbour", "Island views east of the Bridge", "paid", "Ticketed with ferry. Sell out early", -33.8622, 151.2421),
    ("Cockatoo Island", "On the harbour", "Western harbour views", "paid", "For accommodation and camping guests", -33.8477, 151.1717),
    ("Thornton Park, Illoura Reserve and Lookes Ave Reserve", "Balmain East", "Western view of the Bridge", "free", "Family-friendly. Some allow BYO alcohol", -33.8572, 151.1932),
    ("Birchgrove parks", "Birchgrove", "Western harbour", "free", "Quieter, with a local feel", -33.8523, 151.1813),
    ("Pyrmont Bay Park and Darling Harbour", "Pyrmont", "City and Darling Harbour", "free", "Close to restaurants and transport", -33.8690, 151.1966),
]
PILL = {
    "free": ("Free", "free"),
    "free-t": ("Free, ticketed", "free"),
    "paid": ("Paid ticket", "paid"),
    "check": ("Check entry", "check"),
}


def pill(t):
    label, cls = PILL[t]
    return f'<span class="pill pill--{cls}">{label}</span>'


# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------
def marquee():
    links = "".join(
        f'<a href="/?area={escape(a)}#directory">{escape(a)}</a>{icon("sparkle")}' for a in AREAS
    )
    dup = re.sub(r'<a ', '<a tabindex="-1" ', links)
    return f"""<nav class="marquee" aria-label="Browse events by area"><div class="mq-track">{links}</div><div class="mq-track" aria-hidden="true">{dup}</div></nav>"""


def featured_rail(featured):
    cards = "".join(
        f"""<a class="rc reveal" style="--i:{i};--gx:{(i * 37) % 100}%;--gy:{(i * 53) % 100}%" href="/events/{e['slug']}/">
<span class="rc-loc">{icon("map-pin")} {escape(e['suburb'])}</span>
<h3>{escape(e['name'])}</h3>
<p>{escape(e['blurb'])}</p>
<span class="rc-foot"><span class="rc-price">{money(e['price_from']) if e['price_from'] is not None else 'TBA'}</span><span class="rc-fw">{icon("sparkle")} {escape(e['fireworks'])}</span></span>
</a>""" for i, e in enumerate(featured)
    )
    return f"""<section class="sec sec--rail"><div class="wrap rail-head">
<h2 class="reveal">Featured this year</h2>
<div class="rail-btns"><button class="icon-btn" data-rail="-1" aria-label="Previous featured events">{icon("arrow-left")}</button><button class="icon-btn" data-rail="1" aria-label="Next featured events">{icon("arrow-right")}</button></div>
</div>
<div class="rail" data-rail-track tabindex="0" role="region" aria-label="Featured events">{cards}</div></section>"""


def bento():
    cells = [
        ("b-dinner", "bridge", "/new-years-eve-dinner-sydney/", "Dinners with a view", "From a $99 hotel buffet to degustations at Bennelong and Altitude.", "See dinners"),
        ("b-cruise", "reflections", "/new-years-eve-cruises-sydney/", "Out on the water", "Cruises that sit among the barges for both shows.", "See cruises"),
        ("b-party", "red", "/new-years-eve-parties-sydney/", "Parties and rooftops", "Opera Bar, Luna Park and the Bondi Beach party.", "See parties"),
        ("b-family", None, "/family-new-years-eve-sydney/", "Home by ten", "The 9pm Family Fireworks, ticketed parks and Taronga.", "See family picks"),
    ]
    out = ""
    for i, (cls, photo, href, h, p, cta) in enumerate(cells):
        media = f'<div class="b-media">{img(photo, "", sizes="(max-width: 768px) 100vw, 50vw")}</div>' if photo else '<div class="b-glow" aria-hidden="true"></div>'
        out += f'<a class="b {cls} reveal" style="--i:{i}" href="{href}">{media}<div class="b-copy"><h3>{h}</h3><p>{p}</p><span class="b-go">{cta} {ARROW}</span></div></a>'
    return f"""<section class="sec"><div class="wrap">
<div class="sec-head split"><h2 class="reveal">Pick your kind of night</h2><p class="reveal" style="--i:1">Four ways to see in {NY}, from a harbourside table to a picnic rug under the Bridge.</p></div>
<div class="bento">{out}</div></div></section>"""


def vantage_teaser():
    rows = "".join(
        f'<li><div><b>{escape(n)}</b><span>{escape(a)}</span></div>{pill(t)}</li>' for n, a, v, t, note, *_ in VANTAGE[:6]
    )
    return f"""<section class="sec"><div class="wrap zig">
<figure class="zig-media reveal">{img("fleet", "", sizes="(max-width: 768px) 100vw, 50vw")}</figure>
<div class="zig-copy"><h2 class="reveal">Where to watch for free</h2>
<p class="reveal" style="--i:1">Over a million people line the foreshore. Here's where to set up, and which spots fill first.</p>
<ul class="vlist reveal" style="--i:2">{rows}</ul>
<a class="btn btn-ghost reveal" style="--i:3" href="/sydney-fireworks-vantage-points/">Open the vantage map {ARROW}</a></div>
</div></section>"""


def page_home():
    featured = [e for e in EVENTS if e.get("featured")]
    rest = [e for e in EVENTS if not e.get("featured")]
    ordered = featured + rest
    n = len(EVENTS)
    h1 = words("NYE in Sydney", start=0) + " " + words(str(Y), accent={str(Y)}, start=3)
    body = f"""
{hero("fleet", h1, f"NYE in Sydney, sorted: {n} dinners, cruises, parties and vantage points for Sydney New Year's Eve. Compare and book direct.",
      f'<a class="btn btn-gold" href="#directory">Browse events {ARROW}</a><a class="btn btn-ghost" href="/sydney-fireworks-vantage-points/">Vantage points</a>',
      aside=countdown("lg") + deadline(), pos="60% 40%")}
{marquee()}
{featured_rail(featured)}
{bento()}
{directory(ordered, f"Every Sydney NYE {Y} event", "Filter by type, area or budget. Every listing shows the price, what's included and which fireworks you'll see.")}
{night_story("The night, hour by hour", "Scroll through 31 December. Timings follow recent years and are confirmed by the City of Sydney in December.")}
{vantage_teaser()}
{list_band()}
{faq_block(FAQ, "Questions, answered", "The things people ask most before the big night.")}
"""
    return layout(
        "/",
        f"NYE in Sydney {Y}: New Year's Eve Fireworks, Events & Dinners",
        f"NYE in Sydney {Y}: the live countdown, 9pm and midnight fireworks times, the best vantage points and {n}+ bookable New Year's Eve dinners, harbour cruises and parties.",
        body,
        head_extra=f'<link rel="preload" as="image" href="/img/{PHOTOS["fleet"]["file"]}-1920.webp" imagesrcset="/img/{PHOTOS["fleet"]["file"]}-960.webp 960w, /img/{PHOTOS["fleet"]["file"]}-1920.webp 1920w" imagesizes="100vw">',
        schema=[item_list(ordered, f"Sydney New Year's Eve {Y} events"), faq_schema(FAQ),
                {"@context": "https://schema.org", "@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/",
                 "logo": URL + "/favicon.svg", "email": CONFIG["contact_email"]}],
    )


CATEGORY_PAGES = [
    {
        "path": "/new-years-eve-dinner-sydney/", "more": "Want to compare a dinner with a cruise or a party? Our {link} puts every option side by side.", "anchor": 1, "photo": "bridge", "pos": "50% 30%",
        "filter": lambda e: "dining" in e["categories"] or "fine-dining" in e["categories"],
        "title": f"New Year's Eve Dinner Sydney {Y}: Restaurants with Fireworks Views",
        "h1": ("New Year's Eve dinners in Sydney", None),
        "short": "Harbourside tables, NYE degustations and early sittings with a view of the fireworks.",
        "desc": f"The best New Year's Eve dinners in Sydney {Y}: harbourside restaurants with fireworks views, NYE degustations, early sittings and set menus, with prices and booking links.",
        "intro": "A harbourside table is the most comfortable way to watch the fireworks: no camping out, no crowds, and a long dinner while you wait for midnight. Early sittings usually include the 9pm show and cost far less, while late sittings take you through to the midnight fireworks.",
        "tips": ["Book early. The best harbourfront tables sell out months ahead.", "Early sittings are the best-value way to get a harbour view, and many include the 9pm show.", "Ask whether your table is guaranteed a fireworks view or only the venue is.", "Allow extra travel time, as road closures start in the afternoon."],
    },
    {
        "path": "/new-years-eve-cruises-sydney/", "more": "Not sold on the water? Browse {link}, from harbourside dinners to free vantage points.", "anchor": 2, "photo": "reflections", "pos": "50% 40%",
        "filter": lambda e: "cruise" in e["categories"],
        "title": f"Sydney NYE Cruises {Y}: Harbour Fireworks Dinner Cruises",
        "h1": ("Sydney Harbour New Year's Eve cruises", None),
        "short": "Dinner cruises, glass boats and party catamarans that sit among the barges for both shows.",
        "desc": f"Compare Sydney Harbour New Year's Eve cruises for {Y}: dinner cruises, glass boats and party catamarans that cover both the 9pm and midnight fireworks.",
        "intro": "Being on the water is the closest you can get to the fireworks barges. NYE cruises normally board in the late afternoon, include dinner and drinks, and stay out for both the 9pm and midnight displays. Boats take up positions in exclusion zones set by NSW Maritime, so the operator's licence and position matter.",
        "tips": ["Check where the vessel will sit for the midnight show.", "Compare boarding wharf and return times, as transport after midnight is busy.", "Smaller capacity means more deck space at midnight.", "Most NYE cruises are 18+. Check before booking for families."],
    },
    {
        "path": "/new-years-eve-parties-sydney/", "more": "Looking for something calmer? The {link} also covers dinners, cruises and family picks.", "anchor": 3, "photo": "red", "pos": "50% 40%",
        "filter": lambda e: "party" in e["categories"] or "rooftop" in e["categories"],
        "title": f"Sydney NYE Parties {Y}: Best New Year's Eve Parties & Rooftops",
        "h1": ("The best New Year's Eve parties in Sydney", None),
        "short": "Opera Bar, Luna Park, rooftop bars, clubs and the Bondi Beach party, with prices and tickets.",
        "desc": f"Sydney's best New Year's Eve parties for {Y}: Opera Bar, Luna Park, rooftop bars, clubs and the Bondi Beach party, with prices, inclusions and tickets.",
        "intro": "From the Opera House to Bondi Beach, these are the best NYE parties in Sydney. Some sit right on the harbour with a full view of the fireworks. Others are rooftops, clubs and pubs where midnight is just part of the night.",
        "tips": ["Many parties release tickets in tiers, so the first release is the cheapest.", "Check whether drinks are included or pay-as-you-go.", "Most parties are 18+ with ID checks.", "Look for 'guaranteed fireworks view' if the view matters to you."],
    },
    {
        "path": "/family-new-years-eve-sydney/", "more": "For grown-up plans after the kids are asleep, see all the {link} in one place.", "anchor": 4, "photo": "fleet", "pos": "30% 60%",
        "filter": lambda e: "family" in e["categories"] or "vantage" in e["categories"],
        "title": f"Family New Year's Eve Sydney {Y}: Kid-Friendly NYE & 9pm Fireworks",
        "h1": ("Family-friendly New Year's Eve in Sydney", None),
        "short": "The 9pm Family Fireworks, ticketed parks with facilities, Taronga Zoo and early dinners.",
        "desc": f"Kid-friendly ways to celebrate New Year's Eve {Y} in Sydney: 9pm Family Fireworks, ticketed parks, Taronga Zoo and family dinners.",
        "intro": "The 9pm Family Fireworks were designed for kids, so you can see a full harbour show and be home in bed before midnight. Ticketed parks give you guaranteed space, toilets and food, which makes a big difference with little ones.",
        "tips": ["Aim for the 9pm Family Fireworks with younger kids.", "Ticketed parks guarantee space and facilities, so you don't need to arrive at dawn.", "Pack hats, sunscreen, water, a picnic rug and ear protection for little ones.", "Agree on a meeting point in case anyone gets separated."],
    },
]


HOME_ANCHORS = ["NYE in Sydney", "NYE in Sydney guide", "every NYE in Sydney event", "full NYE in Sydney directory", "NYE in Sydney events"]


def home_link(i):
    return f'<a href="/">{HOME_ANCHORS[i % len(HOME_ANCHORS)]}</a>'


def lede(intro, tips, side_title, more=""):
    t = "".join(f'<li class="reveal" style="--i:{i}">{icon("check")}<span>{x}</span></li>' for i, x in enumerate(tips))
    return f"""<section class="sec sec--tight"><div class="wrap lede">
<div><p class="lede-text reveal">{intro}</p>{f'<p class="lede-more reveal" style="--i:1">{more}</p>' if more else ''}</div>
<div class="lede-tips"><h2 class="reveal">{side_title}</h2><ul class="ticks">{t}</ul></div>
</div></section>"""


def page_category(c):
    events = [e for e in EVENTS if c["filter"](e)]
    events.sort(key=lambda e: (not e.get("featured"), e["price_from"] if e["price_from"] is not None else 1e9))
    h1 = words(c["h1"][0]) + " " + words(str(Y), accent={str(Y)}, start=len(c["h1"][0].split()))
    body = f"""
{hero(c["photo"], h1, c["short"], f'<a class="btn btn-gold" href="#directory">Browse events {ARROW}</a><a class="btn btn-ghost" href="/list-your-event/">List your event</a>',
      aside=countdown("md") + deadline(), kind="page", pos=c["pos"], crumbs=crumb_html(("Home", "/"), (c["h1"][0], c["path"])))}
{lede(c["intro"], c["tips"], "Booking tips", c["more"].format(link=home_link(c["anchor"])))}
{directory(events, f"{len(events)} options, compared", "Prices are per person, from published packages. Confirm the current price with the venue.")}
{list_band()}"""
    return layout(
        c["path"], c["title"] + " | NYE in Sydney", c["desc"], body,
        head_extra=f'<link rel="preload" as="image" href="/img/{PHOTOS[c["photo"]]["file"]}-1920.webp" imagesrcset="/img/{PHOTOS[c["photo"]]["file"]}-960.webp 960w, /img/{PHOTOS[c["photo"]]["file"]}-1920.webp 1920w" imagesizes="100vw">',
        schema=[item_list(events, c["h1"][0]), breadcrumbs(("Home", "/"), (c["h1"][0], c["path"]))],
    )


def page_event(e):
    path = f"/events/{e['slug']}/"
    inc = "".join(f'<li class="reveal" style="--i:{i}">{icon("check")}<span>{escape(x)}</span></li>' for i, x in enumerate(e["includes"]))
    cats = ", ".join(CATEGORY_LABELS.get(c, c) for c in e["categories"])
    related = [x for x in EVENTS if x["slug"] != e["slug"] and (x["area"] == e["area"] or set(x["categories"]) & set(e["categories"]))][:3]
    photo = next((CAT_PHOTO[c] for c in e["categories"] if c in CAT_PHOTO), "fleet")
    offer = {"@type": "Offer", "url": e["url"], "priceCurrency": "AUD", "availability": "https://schema.org/InStock",
             "validFrom": f"{Y}-01-01"}
    if e["price_from"] is not None:
        offer["price"] = e["price_from"]
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"{e['name']}: New Year's Eve {Y}",
        "description": e["blurb"] + " Includes: " + "; ".join(e["includes"]) + ".",
        "startDate": f"{Y}-12-31",
        "endDate": f"{NY}-01-01",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": [f"{URL}/img/{PHOTOS[photo]['file']}-1920.webp", f"{URL}/og.jpg"],
        "location": {
            "@type": "Place", "name": e["venue"],
            "address": {"@type": "PostalAddress", "addressLocality": e["suburb"], "addressRegion": "NSW", "addressCountry": "AU"},
        },
        "organizer": {"@type": "Organization", "name": e["venue"].split(",")[0], "url": e["url"]},
        "offers": offer,
    }
    price_big = "Free" if e["price_from"] == 0 else money(e["price_from"]) if e["price_from"] else "TBA"
    body = f"""
{hero(photo, words(e['name']), escape(e['blurb']),
      f'<a class="btn btn-gold" href="{e["url"]}" target="_blank" rel="noopener sponsored">Book with the venue {icon("arrow-up-right")}</a><a class="btn btn-ghost" href="/#directory">All events</a>',
      kind="page", crumbs=crumb_html(("Home", "/"), ("Events", "/#directory"), (e["name"], path)))}
<section class="sec sec--tight"><div class="wrap event-layout">
<div class="event-main">
<h2 class="reveal">What's included</h2>
<ul class="ticks ticks--lg">{inc}</ul>
<div class="prose reveal">
<h2>About {escape(e['name'])}</h2>
<p>{escape(e['name'])} is at {escape(e['venue'])} in {escape(e['suburb'])} ({escape(e['area'])}). It's one of the {escape(cats.lower())} options for New Year's Eve {Y} in Sydney. Fireworks: <b>{escape(e['fireworks'])}</b>. Age: <b>{escape(e['age'])}</b>.</p>
<p>Still deciding? Compare it with {home_link(EVENTS.index(e))} or browse <a href="/sydney-fireworks-vantage-points/">vantage points around the harbour</a>. For the night itself, check the <a href="/plan-your-night/">fireworks timeline and transport tips</a>.</p>
<p class="notice">Details are based on the venue's published NYE information and can change. Confirm the price, times and inclusions with {escape(e['venue'].split(',')[0])} before booking. Are you the venue? <a href="/list-your-event/">Claim and upgrade this listing</a>.</p>
</div></div>
<aside class="side reveal" style="--i:2">
<div class="side-price"><b>{price_big}</b><span>{escape(e['price_text'])}</span></div>
<dl><dt>Date</dt><dd>Thursday 31 December {Y}</dd><dt>Time</dt><dd>{escape(e['time'])}</dd>
<dt>Where</dt><dd>{escape(e['venue'])}</dd><dt>Fireworks</dt><dd>{escape(e['fireworks'])}</dd><dt>Age</dt><dd>{escape(e['age'])}</dd></dl>
<a class="btn btn-gold btn-block" href="{e['url']}" target="_blank" rel="noopener sponsored">Book with the venue {icon("arrow-up-right")}</a>
{countdown("sm")}
</aside>
</div></section>
<section class="sec"><div class="wrap"><div class="sec-head"><h2 class="reveal">You might also like</h2></div>
<div class="ev-grid">{''.join(card(x, i) for i, x in enumerate(related))}</div></div></section>
{list_band()}"""
    return layout(
        path,
        (f"{e['name']} {Y}" if "NYE" in e["name"] or "New Year" in e["name"] else f"{e['name']} NYE {Y}")
        + f", {e['suburb']} | NYE in Sydney",
        f"{e['name']} New Year's Eve {Y} in {e['suburb']}: {e['price_text']}. {e['blurb']}"[:300],
        body, og_type="article", active="/#directory",
        schema=[schema, breadcrumbs(("Home", "/"), ("NYE events", "/#directory"), (e["name"], path))],
    )


def page_vantage():
    vp = [e for e in EVENTS if "vantage" in e["categories"]]
    faq = FAQ[1:3] + FAQ[5:6] + FAQ[7:8]
    points = [{"n": n, "a": a, "v": v, "t": PILL[t][0], "k": PILL[t][1], "note": note, "lat": lat, "lng": lng}
              for n, a, v, t, note, lat, lng in VANTAGE]
    rows = "".join(
        f'<li><button class="vp" data-vp="{i}"><span class="vp-top"><b>{escape(n)}</b>{pill(t)}</span><span class="vp-meta">{escape(a)}. {escape(v)}.</span><span class="vp-note">{escape(note)}</span></button></li>'
        for i, (n, a, v, t, note, *_) in enumerate(VANTAGE)
    )
    body = f"""
{hero("fleet", words("Sydney fireworks vantage points") + " " + words(str(Y), accent={str(Y)}, start=4),
      "Free foreshore parks, free-ticketed islands and paid spots with guaranteed entry, mapped.",
      f'<a class="btn btn-gold" href="#map">Open the map {ARROW}</a><a class="btn btn-ghost" href="#ticketed">Ticketed spots</a>',
      aside=countdown("md") + deadline(), kind="page", pos="40% 70%",
      crumbs=crumb_html(("Home", "/"), ("Vantage points", "/sydney-fireworks-vantage-points/")))}
<section class="sec" id="map"><div class="wrap">
<div class="sec-head split"><h2 class="reveal">The harbour, mapped</h2><p class="reveal" style="--i:1">Pick a spot to fly to it. Capacity and entry rules are set each year by the City of Sydney, the NSW Government and local councils.</p></div>
<div class="map-wrap reveal"><div id="vmap" class="vmap" role="region" aria-label="Map of Sydney fireworks vantage points"></div>
<ol class="vps">{rows}</ol></div>
<script type="application/json" id="vp-data">{j(points)}</script>
</div></section>
{directory(vp, "Book a guaranteed spot", "Ticketed vantage points mean no dawn queue. Tickets usually release between September and December.", show_filters=False, anchor="ticketed")}
<section class="sec sec--tight"><div class="wrap lede">
<div class="prose reveal">
<h2>How to choose a vantage point</h2>
<p><b>For the classic shot</b> with the Opera House and Harbour Bridge together, look west from Mrs Macquaries Point or east from Blues Point and McMahons Point.</p>
<p><b>To be close to the Bridge</b>, go for Hickson Road Reserve, Lower Bradfield Park or Luna Park. The midnight show launches straight off the Bridge.</p>
<p><b>For space and a quieter night</b>, try the Balmain East and Birchgrove parks, the islands (ferry plus ticket), or elevated eastern spots like Dudley Page Reserve.</p>
<p><b>With kids</b>, a ticketed park gives you guaranteed space, toilets and food. Make the 9pm Family Fireworks your main event.</p>
<p><b>Rather have a table or a deck?</b> Our <a href="/">NYE in Sydney guide</a> lists every harbourside dinner, cruise and party with a fireworks view.</p></div>
<div class="lede-tips"><h2 class="reveal">What to bring</h2><ul class="ticks">
<li>{icon("check")}<span>Picnic rug and low chair (check whether chairs are allowed)</span></li><li>{icon("check")}<span>Water, snacks and sunscreen. You may be outdoors for 10+ hours</span></li>
<li>{icon("check")}<span>Charged phone and a power bank</span></li><li>{icon("check")}<span>A light jacket for after dark</span></li><li>{icon("check")}<span>No glass. Check the alcohol rules for your site</span></li></ul></div>
</div></section>
{faq_block(faq, "Vantage point questions", "Free or ticketed, early or late: what to know before you pick a spot.")}
{list_band()}"""
    head = ('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">'
            '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin="" defer></script>')
    return layout(
        "/sydney-fireworks-vantage-points/",
        f"Sydney NYE Fireworks Vantage Points {Y}: Best Free & Ticketed Spots | NYE in Sydney",
        f"The best places to watch the Sydney New Year's Eve fireworks in {Y}: a map of free harbour vantage points, free-ticketed islands and $65 ticketed parks, plus what time to arrive.",
        body, head_extra=head, schema=[faq_schema(faq), item_list(vp, "Ticketed vantage points"),
                                       breadcrumbs(("Home", "/"), ("Vantage points", "/sydney-fireworks-vantage-points/"))],
    )


def page_plan():
    faq = [FAQ[0], FAQ[6], FAQ[7], FAQ[8]]
    body = f"""
{hero("reflections", words("Plan your Sydney NYE") + " " + words(str(Y), accent={str(Y)}, start=4),
      "Fireworks times, the night's run sheet, transport, road closures and what to bring.",
      f'<a class="btn btn-gold" href="#night">See the timeline {ARROW}</a><a class="btn btn-ghost" href="#transport">Transport</a>',
      aside=countdown("md") + deadline(), kind="page", crumbs=crumb_html(("Home", "/"), ("Plan your night", "/plan-your-night/")))}
{night_story("Fireworks times and the night's schedule", f"Based on recent years. The City of Sydney publishes the final {Y} program in December.")}
<section class="sec sec--tight" id="transport"><div class="wrap prose prose--wide reveal">
<p>Once you know how you're getting there, pick where you're going from <a href="/">every NYE in Sydney event</a> in our directory.</p>
<h2>Getting there by public transport</h2>
<p>Public transport is the best way to get to and from the harbour on New Year's Eve. Extra trains, buses, ferries and light rail run through the evening and all night. Stations near the harbour, especially Circular Quay, Wynyard and Milsons Point, get extremely busy and may close temporarily or run one-way to manage crowds.</p>
<ul><li>Plan your trip on <a href="https://transportnsw.info" rel="noopener" target="_blank">transportnsw.info</a> and check the special NYE timetable.</li>
<li>Have a back-up station in mind. Walking 10 to 15 minutes to a quieter station often saves an hour.</li>
<li>After midnight, expect queues. Stay for a drink or snack and leave once the first wave has gone.</li></ul>
<h2 id="roads">Road closures and driving</h2>
<p>Big parts of the CBD, The Rocks, North Sydney and roads around the Harbour Bridge close from the afternoon of 31 December until the early hours of 1 January. Parking near the harbour is close to impossible. If you have to drive, park well outside the closure zone and finish the trip by public transport.</p>
<h2 id="boating">Boating on the harbour</h2>
<p>Private boats must follow NSW Maritime exclusion zones and NYE rules, and the harbour is very busy. For most people a licensed <a href="/new-years-eve-cruises-sydney/">NYE cruise</a> is the easiest way to see the show from the water.</p>
<h2 id="accessibility">Accessibility</h2>
<p>Several vantage points have accessible viewing areas, accessible toilets and companion access. These spaces are limited, so plan ahead and check the official accessibility information for your site. Many harbourside venues in our directory have step-free access. Contact the venue to confirm.</p>
<h2>Safety and wellbeing</h2>
<ul><li>Drink plenty of water. It's usually a hot day and a long night.</li><li>Agree on a meeting point with your group.</li><li>Follow police and staff directions. Sites close when full.</li><li>Look after your mates, and get help from first-aid stations if you need it.</li></ul>
</div></section>
{faq_block(faq, "Planning questions", "Times, transport and the rules on the night.")}
{list_band()}"""
    return layout(
        "/plan-your-night/",
        f"Sydney NYE {Y} Fireworks Times, Transport & Planning Guide | NYE in Sydney",
        f"Sydney New Year's Eve {Y} planning guide: 9pm and midnight fireworks times, the schedule for the night, public transport, road closures, accessibility and what to bring.",
        body, schema=[faq_schema(faq), breadcrumbs(("Home", "/"), ("Plan your night", "/plan-your-night/"))],
    )


def season_section():
    months = [
        ("October", "Planning begins", "Big parties, cruises and ticketed spots release tickets, and Sydney starts searching \"NYE in Sydney\". Groups start comparing options.", "List now and you're live for the whole season."),
        ("November", "Comparing and booking", "Searchers compare prices, inclusions and views side by side. Premium tables, cruises and party tickets get booked.", "Your price, inclusions and Book button win the comparison."),
        ("December", "Peak searches, last-minute rush", "Search interest peaks. People chase the last tables, final release tiers and late tickets right up to 31 December.", "Sell your remaining tickets while demand is at its highest."),
    ]
    cols = "".join(
        f"""<div class="mo mo-{i} reveal" style="--i:{i}"><div class="mo-bar" aria-hidden="true"><span></span></div>
<h3><span>{m}</span>{t}</h3><p>{d}</p><p class="mo-win">{icon("arrow-right")} {w}</p></div>""" for i, (m, t, d, w) in enumerate(months)
    )
    return f"""<section class="sec" id="season"><div class="wrap">
<div class="sec-head split"><h2 class="reveal">Sydney books New Year's Eve in three months</h2>
<p class="reveal" style="--i:1">Searches like "NYE in Sydney", "Sydney New Year's Eve" and "NYE dinner Sydney" climb from October and peak in late December. That's when people choose and buy.</p></div>
<div class="months">{cols}</div>
<p class="fineprint reveal">Bars show the typical seasonal pattern of search interest, not exact volumes.</p>
</div></section>"""


def page_list():
    has_pay = "YOUR_" not in CONFIG["payment_link"]
    form_sub = (f"Fill this in, then pay ${P} securely. We'll publish your page and email you the link." if has_pay
                else f"Fill this in and we'll email you a ${P} invoice within one business day. Your page goes live once it's paid.")
    submit_label = f"Continue to payment, ${P}" if has_pay else "Send my listing request"
    cats = "".join(f'<option value="{k}">{v}</option>' for k, v in CATEGORY_LABELS.items() if k not in ("budget", "free"))
    faq = [
        ("What do I get for $" + str(P) + "?", "A dedicated event page built for search, with Google Event structured data. You also get a listing in our main directory and the matching category pages (dinners, cruises, parties, family), a direct link to your own booking page, and edits until 31 December."),
        ("Why should I list now rather than in December?", "Search interest in Sydney New Year's Eve builds from October and peaks in the final weeks of December. Listing early means your page is live and indexed by Google for the whole season, not just the last-minute rush. New pages can take days or weeks to rank, so the earlier you're in, the more of the season you capture. It's the same $" + str(P) + " whenever you list."),
        ("Do you take commission on bookings?", "No. Guests book directly with you through your own link, and you keep 100% of every ticket."),
        ("How long does my listing stay live?", f"Your listing stays live until New Year's Day {NY}, then rolls into our archive. Previous listers get first right to renew for next year."),
        ("How fast will my listing go live?", "Usually within one business day of payment. We'll email you the link."),
        ("Can I update prices or details?", "Yes. Email us any changes (sold-out tiers, price releases, new acts) and we'll update your page."),
    ]
    why = [
        ("target", "High-intent visitors", "People only visit a NYE guide when they're about to book."),
        ("magnifying-glass", "Our name is the search", '<a href="/">NYE in Sydney</a> is built around the exact phrases people type into Google.'),
        ("file-text", "Your own SEO page", "A dedicated page with Google Event schema, eligible for event rich results."),
        ("squares-four", "Listed where people browse", "The main directory plus every matching category page."),
        ("hand-coins", "Zero commission", "Guests click straight through to your booking page."),
        ("pencil-simple", "Updates until NYE", "Change prices, add tiers or mark sold-out tiers any time."),
    ]
    why_html = "".join(
        f'<li class="reveal" style="--i:{i}">{icon(ic)}<div><b>{t}</b><span>{d}</span></div></li>' for i, (ic, t, d) in enumerate(why)
    )
    h1 = words("List your New Year's Eve event")
    body = f"""
{hero("bridge", h1, "October to December is when Sydney searches for NYE plans. Be the event they find.",
      f'<a class="btn btn-gold" href="#form">List your event {ARROW}</a><a class="btn btn-ghost" href="#season">See the season</a>',
      aside=countdown("md", "left to sell this season") + deadline(), kind="page", pos="50% 35%",
      crumbs=crumb_html(("Home", "/"), ("List your event", "/list-your-event/")))}
{season_section()}
<section class="sec"><div class="wrap offer">
<div class="offer-why"><h2 class="reveal">Why venues list here</h2><ul class="why">{why_html}</ul>
<p class="payoff reveal">At typical harbourside NYE prices of $300 to $850 a head, a couple of bookings covers your ${P} listing. Everything after that is yours.</p></div>
<div class="ticket reveal" style="--i:2">
<div class="ticket-main">
<p class="ticket-kicker">Admit one listing, NYE {Y}</p>
<div class="ticket-amt"><sup>$</sup>{P}</div>
<p class="ticket-sub">AUD inc GST. One-off. No commission.</p>
<ul class="ticks">
<li>{icon("check")}<span>Dedicated event page with Google Event schema</span></li>
<li>{icon("check")}<span>Directory and category page placement</span></li>
<li>{icon("check")}<span>Book button straight to your site</span></li>
<li>{icon("check")}<span>Unlimited edits until 31 December</span></li>
<li>{icon("check")}<span>Live within one business day</span></li>
</ul></div>
<div class="ticket-stub"><span>Valid Oct to Dec {Y}</span><a class="btn btn-gold btn-block" href="#form">List your event {ARROW}</a></div>
</div>
</div></section>
<section class="sec" id="form"><div class="wrap form-wrap">
<div class="sec-head"><h2 class="reveal">Your event details</h2><p class="reveal" style="--i:1">{form_sub}</p></div>
<form class="listing reveal" data-endpoint="{CONFIG['form_endpoint']}" data-payment="{CONFIG['payment_link']}" data-email="{CONFIG['contact_email']}">
<div class="fld"><label for="f-name">Event name *</label><input id="f-name" name="event_name" required></div>
<div class="fld"><label for="f-venue">Venue *</label><input id="f-venue" name="venue" required></div>
<div class="fld"><label for="f-suburb">Suburb *</label><input id="f-suburb" name="suburb" required></div>
<div class="fld"><label for="f-cat">Type *</label><select id="f-cat" name="category" required>{cats}</select></div>
<div class="fld"><label for="f-price">Price from (AUD pp)</label><input id="f-price" name="price_from" inputmode="decimal" placeholder="249"></div>
<div class="fld"><label for="f-time">Times</label><input id="f-time" name="times" placeholder="7pm to 1am"></div>
<div class="fld"><label for="f-fw">Fireworks view</label><select id="f-fw" name="fireworks"><option>Both 9pm and midnight</option><option>Midnight only</option><option>9pm only</option><option>Partial or nearby</option><option>No view</option></select></div>
<div class="fld"><label for="f-age">Age</label><select id="f-age" name="age"><option>18+</option><option>All ages</option><option>Family-friendly</option></select></div>
<div class="fld full"><label for="f-url">Booking URL *</label><input id="f-url" name="booking_url" type="url" required placeholder="https://"></div>
<div class="fld full"><label for="f-desc">Description and inclusions *</label><textarea id="f-desc" name="description" required placeholder="Food, drinks, DJs, views. What makes your night special?"></textarea></div>
<div class="fld"><label for="f-contact">Contact name *</label><input id="f-contact" name="contact_name" required></div>
<div class="fld"><label for="f-email">Email *</label><input id="f-email" name="email" type="email" required></div>
<div class="fld"><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel"></div>
<div class="fld"><label for="f-abn">Business or ABN</label><input id="f-abn" name="business"></div>
<input type="hidden" name="_subject" value="New NYE in Sydney listing request (${P})">
<input type="hidden" name="_template" value="table"><input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="fld full"><button class="btn btn-gold" type="submit">{submit_label} {ARROW}</button>
<p class="form-status" aria-live="polite"></p></div>
</form></div></section>
{faq_block(faq, "Listing questions", "Everything venues ask before they list.")}"""
    service = {
        "@context": "https://schema.org", "@type": "Service", "name": f"NYE {Y} event listing",
        "provider": {"@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/"},
        "areaServed": "Sydney, NSW",
        "offers": {"@type": "Offer", "price": P, "priceCurrency": "AUD", "url": URL + "/list-your-event/"},
    }
    return layout(
        "/list-your-event/",
        f"List Your New Year's Eve Event in Sydney, ${P} | NYE in Sydney",
        f"Promote your Sydney New Year's Eve {Y} party, dinner or cruise. ${P} flat fee, no commission: a dedicated SEO event page, directory placement and a direct booking link.",
        body, schema=[service, faq_schema(faq), breadcrumbs(("Home", "/"), ("List your event", "/list-your-event/"))],
    )


def page_about():
    body = f"""
{hero("reflections", words("About NYE in Sydney"), "An independent guide to the harbour's biggest night, built for people planning it.",
      f'<a class="btn btn-gold" href="/">Browse events {ARROW}</a><a class="btn btn-ghost" href="/list-your-event/">List your event</a>',
      kind="page", crumbs=crumb_html(("Home", "/"), ("About", "/about/")))}
<section class="sec sec--tight"><div class="wrap lede">
<div class="prose reveal">
<h2>What we do</h2>
<p>NYE in Sydney brings every way to see in the new year on Sydney Harbour into one place. That means harbourside dinners, fireworks cruises, rooftop parties, family picks and the official vantage points, each with its price, what's included and which fireworks you'll see.</p>
<p>Start with the <a href="/">NYE in Sydney</a> directory, then filter by area, budget or type. Every listing links straight to the venue to book. We don't take commission, so the price you see is the venue's price.</p>
<h2>Independent, not official</h2>
<p>We're an independent guide. The fireworks and official vantage points are run by the City of Sydney, which publishes the final program in December. We follow its announcements and update our <a href="/plan-your-night/">planning guide</a> and <a href="/sydney-fireworks-vantage-points/">vantage points map</a> as details are confirmed.</p>
<h2>For venues</h2>
<p>If you run a New Year's Eve event in Sydney, you can <a href="/list-your-event/">list it for ${P}</a>. You get your own event page, a place in the directory and a direct booking link, with no commission.</p>
</div>
<div class="lede-tips"><h2 class="reveal">Get in touch</h2><ul class="ticks">
<li>{icon("envelope-simple")}<span><a href="mailto:{CONFIG['contact_email']}">{CONFIG['contact_email']}</a></span></li>
<li>{icon("whatsapp-logo")}<span><a href="https://wa.me/61488898835" target="_blank" rel="noopener">WhatsApp +61 488 898 835</a></span></li>
<li>{icon("clock")}<span>We reply within one business day</span></li></ul></div>
</div></section>
{list_band()}"""
    return layout(
        "/about/",
        f"About NYE in Sydney: Independent Sydney New Year's Eve Guide",
        f"About NYE in Sydney, the independent guide to Sydney New Year's Eve {Y}: how we list dinners, cruises, parties and vantage points, and how venues can list their event.",
        body, schema=[breadcrumbs(("Home", "/"), ("About", "/about/")),
                      {"@context": "https://schema.org", "@type": "AboutPage", "name": "About NYE in Sydney", "url": URL + "/about/"}],
    )


def page_404():
    body = hero("red", words("This page fizzled out"), "The page you're after isn't here, but the fireworks still are.",
                f'<a class="btn btn-gold" href="/">Back to all events {ARROW}</a>', aside=countdown("md") + deadline(), kind="page")
    return layout("/404.html", "Page not found | NYE in Sydney", "Page not found.", body).replace(
        'content="index,follow', 'content="noindex,follow')


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0b0e15"/><g stroke="#e3ac4c" stroke-linecap="round" stroke-width="3.5"><path d="M32 30V10"/><path d="M33.5 30.5 47 17"/><path d="M34 32h20"/><path d="M33.5 33.5 47 47"/><path d="M32 34v20"/><path d="M30.5 33.5 17 47"/><path d="M30 32H10"/><path d="M30.5 30.5 17 17"/></g><circle cx="32" cy="32" r="3.5" fill="#f2ead9"/></svg>"""

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700..800&family=Geist:wght@500&display=swap" rel="stylesheet">
<style>body{{margin:0;width:1200px;height:630px;background:#080a10;color:#f2ead9;font-family:Geist,sans-serif;position:relative;overflow:hidden}}
img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:60% 40%}}
.s{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,10,16,.94) 0%,rgba(8,10,16,.75) 45%,rgba(8,10,16,.1) 100%)}}
.t{{position:absolute;left:72px;top:96px;width:640px}}h1{{font-family:'Bricolage Grotesque',sans-serif;font-size:92px;line-height:.95;letter-spacing:-.03em;margin:0}}
h1 span{{color:#e3ac4c}}p{{font-size:30px;color:#cfc6b4;margin:28px 0 0;line-height:1.35}}
.b{{position:absolute;left:72px;bottom:72px;font-size:24px;color:#e3ac4c;letter-spacing:.02em}}</style></head><body>
<img src="/img/fleet-steps-2023-1920.webp" alt=""><div class="s"></div>
<div class="t"><h1>Sydney New Year's Eve <span>{Y}</span></h1><p>Dinners, cruises, parties and vantage points for the harbour's biggest night.</p></div>
<div class="b">nyeinsydney.com</div>
</body></html>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    pages = {"/": page_home(), "/sydney-fireworks-vantage-points/": page_vantage(),
             "/plan-your-night/": page_plan(), "/list-your-event/": page_list(), "/about/": page_about()}
    for c in CATEGORY_PAGES:
        pages[c["path"]] = page_category(c)
    for e in EVENTS:
        pages[f"/events/{e['slug']}/"] = page_event(e)
    for path, html in pages.items():
        f = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)
    (OUT / "404.html").write_text(page_404())
    shutil.copy(ROOT / "src" / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "src" / "main.js", OUT / "main.js")
    shutil.copytree(ROOT / "src" / "img", OUT / "img")
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / "og.html").write_text(OG_HTML)
    shutil.copy(ROOT / "src" / "og.jpg", OUT / "og.jpg")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /og.html\n\nSitemap: {URL}/sitemap.xml\n")
    prio = lambda p: "1.0" if p == "/" else "0.6" if p.startswith("/events/") else "0.8"
    sm = "".join(
        f"<url><loc>{URL}{p}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{prio(p)}</priority></url>\n"
        for p in pages
    )
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n')
    print(f"Built {len(pages)} pages into {OUT}")


if __name__ == "__main__":
    build()
