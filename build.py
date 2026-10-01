#!/usr/bin/env python3
"""Static site generator for NYE in Sydney.

Edit data/events.json (and the CONFIG block below), then run:
    python3 build.py
The complete site is written to ./docs, which Vercel serves as-is (see vercel.json).
"""
import json
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
    "contact_email": "hello@nyeinsydney.com",
    "listing_price": 599,                              # AUD, inc GST
    # Form backend that stores listing submissions (e.g. Formspree, Basin, Getform).
    # While it still contains "YOUR_", the form falls back to opening an email.
    "form_endpoint": "https://formspree.io/f/YOUR_FORM_ID",
    # Stripe Payment Link (or similar) for the $599 listing fee.
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
    ("/", "Home"),
    ("/#directory", "All events"),
    ("/new-years-eve-dinner-sydney/", "Dinners"),
    ("/new-years-eve-cruises-sydney/", "Cruises"),
    ("/new-years-eve-parties-sydney/", "Parties"),
    ("/sydney-fireworks-vantage-points/", "Vantage points"),
    ("/plan-your-night/", "Plan"),
]


def j(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")


def money(n):
    return "Free" if n == 0 else f"${n:,.0f}"


SKYLINE = """<svg class="skyline" viewBox="0 0 1440 230" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0a26"/><stop offset="1" stop-color="#07061a"/></linearGradient>
<linearGradient id="wt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1450" stop-opacity=".9"/><stop offset="1" stop-color="#07061a"/></linearGradient></defs>
<g fill="url(#sk)">
<rect x="0" y="120" width="40" height="80"/><rect x="44" y="96" width="34" height="104"/><rect x="82" y="130" width="28" height="70"/>
<rect x="114" y="70" width="40" height="130"/><rect x="158" y="108" width="30" height="92"/><rect x="192" y="86" width="26" height="114"/>
<rect x="222" y="124" width="36" height="76"/><rect x="560" y="60" width="36" height="140"/><rect x="600" y="30" width="10" height="40"/>
<circle cx="605" cy="40" r="14"/><rect x="614" y="90" width="40" height="110"/><rect x="658" y="54" width="30" height="146"/>
<rect x="692" y="100" width="44" height="100"/><rect x="740" y="76" width="34" height="124"/><rect x="1290" y="110" width="38" height="90"/>
<rect x="1332" y="84" width="30" height="116"/><rect x="1366" y="126" width="40" height="74"/><rect x="1410" y="100" width="30" height="100"/>
<path d="M280 178 Q300 120 352 104 Q340 140 338 178Z M320 178 Q348 100 410 86 Q392 130 390 178Z M372 178 Q404 96 470 84 Q450 130 446 178Z M430 178 Q460 118 510 110 Q496 146 494 178Z"/>
<rect x="270" y="176" width="250" height="24"/>
<rect x="800" y="108" width="26" height="92"/><rect x="1226" y="108" width="26" height="92"/>
</g>
<g fill="none" stroke="#0c0a26" stroke-width="7"><path d="M826 150 Q1026 10 1226 150"/><path d="M826 150 L1226 150" stroke-width="6"/></g>
<g stroke="#0c0a26" stroke-width="2">""" + "".join(
    f'<line x1="{x}" y1="150" x2="{x}" y2="{150 - (1 - ((x - 1026) / 200) ** 2) * 70:.0f}"/>'
    for x in range(846, 1226, 20)
) + """</g>
<rect x="0" y="198" width="1440" height="32" fill="url(#wt)"/>
</svg>"""


def countdown(mini=False):
    units = [("d", "Days"), ("h", "Hours"), ("m", "Minutes"), ("s", "Seconds")]
    inner = "".join(
        f'<div class="cd-unit"><div class="cd-num" data-u="{k}">--</div><div class="cd-label">{v}</div></div>'
        for k, v in units
    )
    return f'<div class="countdown{" mini" if mini else ""}" data-countdown role="timer" aria-label="Countdown to midnight, New Year\'s Eve {Y} in Sydney">{inner}</div>'


def layout(path, title, description, body, schema=None, og_type="website", active=None):
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
    nav = "".join(
        f'<li><a href="{h}"{cur if h == (active or path) else ""}>{t}</a></li>' for h, t in NAV
    )
    ld = "".join(f'<script type="application/ld+json">{j(s)}</script>' for s in schemas)
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="AU-NSW"><meta name="geo.placename" content="Sydney">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{CONFIG['site_name']}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{URL}/og.png"><meta property="og:locale" content="en_AU">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{URL}/og.png">
<meta name="theme-color" content="#07061a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav"><div class="wrap">
<a class="logo" href="/">NYE <span>in Sydney</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
<a class="btn btn-primary btn-sm" href="/list-your-event/">List your event</a>
<button class="menu-btn" aria-label="Menu" aria-expanded="false">☰</button>
</div></header>
<main id="main">
{body}
</main>
<footer><div class="wrap">
<div class="fgrid">
<div><a class="logo" href="/">NYE <span>in Sydney</span></a>
<p class="muted">The independent guide to New Year's Eve {Y} in Sydney: fireworks vantage points, harbour cruises, dinners and parties, all in one place.</p>
{countdown(mini=True)}</div>
<div><h4>Explore</h4><ul>
<li><a href="/#directory">All NYE events</a></li><li><a href="/new-years-eve-dinner-sydney/">NYE dinners</a></li>
<li><a href="/new-years-eve-cruises-sydney/">NYE cruises</a></li><li><a href="/new-years-eve-parties-sydney/">NYE parties</a></li>
<li><a href="/family-new-years-eve-sydney/">Family NYE</a></li></ul></div>
<div><h4>Plan</h4><ul>
<li><a href="/sydney-fireworks-vantage-points/">Vantage points</a></li><li><a href="/plan-your-night/">Fireworks times</a></li>
<li><a href="/plan-your-night/#transport">Transport</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
<div><h4>Venues</h4><ul>
<li><a href="/list-your-event/">List your event: ${CONFIG['listing_price']}</a></li>
<li><a href="mailto:{CONFIG['contact_email']}">{CONFIG['contact_email']}</a></li></ul></div>
</div>
<p class="fine">NYE in Sydney is an independent guide and is not affiliated with the City of Sydney or the official Sydney New Year's Eve event. Prices and details are supplied by venues or based on published information and may change. Always confirm with the venue before booking. We acknowledge the Gadigal of the Eora Nation, the Traditional Custodians of the land and waters of Sydney Harbour. © {Y} {CONFIG['site_name']}.</p>
</div></footer>
<script src="/main.js" defer></script>
</body>
</html>"""


# --------------------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------------------
def card(e, i):
    cats = " ".join(e["categories"])
    search = " ".join([e["name"], e["venue"], e["suburb"], e["area"], " ".join(e["categories"]), e["blurb"]]).lower()
    tags = "".join(f'<span class="tag">{CATEGORY_LABELS.get(c, c)}</span>' for c in e["categories"][:3])
    price = e["price_from"]
    price_html = (
        "Free<small>ticket required</small>" if price == 0
        else f"{money(price)}<small>from, per person</small>" if price
        else "TBA<small>see venue</small>"
    )
    return f"""<article class="card{' featured' if e.get('featured') else ''}" data-cats="{cats}" data-area="{escape(e['area'])}" data-price="{price if price is not None else ''}" data-featured="{1 if e.get('featured') else 0}" data-order="{i}" data-search="{escape(search)}">
{'<span class="badge">Featured</span>' if e.get('featured') else ''}
<div class="loc">📍 {escape(e['suburb'] if e['suburb'] in e['area'] else e['suburb'] + ' · ' + e['area'])}</div>
<h3><a href="/events/{e['slug']}/">{escape(e['name'])}</a></h3>
<p>{escape(e['blurb'])}</p>
<div class="tags"><span class="tag fw">🎆 {escape(e['fireworks'])}</span>{tags}</div>
<div class="meta"><div class="price">{price_html}</div>
<div class="actions"><a class="btn btn-ghost btn-sm" href="/events/{e['slug']}/">Details</a><a class="btn btn-primary btn-sm" href="{e['url']}" target="_blank" rel="noopener sponsored">Book</a></div></div>
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
    filters = f"""<div class="filters" role="group" aria-label="Filter by type">{chips}</div>
<div class="toolbar"><input id="q" type="search" placeholder="Search venue, suburb, vibe…" aria-label="Search events">
<select id="area" aria-label="Filter by area">{areas}</select>
<select id="sort" aria-label="Sort"><option value="featured">Sort: Featured</option><option value="low">Price: low to high</option><option value="high">Price: high to low</option></select></div>
<p class="count" aria-live="polite"></p>""" if show_filters else ""
    cards = "".join(card(e, i) for i, e in enumerate(events))
    return f"""<section id="{anchor}" data-directory><div class="wrap">
<div class="section-head"><h2>{heading}</h2><p>{sub}</p></div>
{filters}
<div class="grid">{cards}</div>
<p class="empty">No events match that search. Try another filter, or <a href="/list-your-event/">list yours</a>.</p>
</div></section>"""


def list_band():
    return f"""<section><div class="wrap"><div class="band">
<div><h2>Running a NYE event in Sydney?</h2><p>Get in front of people planning their night right now. ${CONFIG['listing_price']} flat, no commission on your bookings.</p></div>
<a class="btn" href="/list-your-event/">List your event →</a></div></div></section>"""


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


# --------------------------------------------------------------------------------------
# Content: FAQ, timeline, vantage points
# --------------------------------------------------------------------------------------
FAQ = [
    (f"What time are the Sydney New Year's Eve fireworks in {Y}?",
     f"There are two main displays on Thursday 31 December {Y}. The 9pm Family Fireworks run for about 8–10 minutes and are made for kids and early nights. The Midnight Fireworks, the main show seen around the world, run for about 12 minutes and launch from the Sydney Harbour Bridge, barges and city rooftops to welcome {NY}."),
    ("Where is the best place to watch the Sydney fireworks?",
     "For the classic Opera House and Harbour Bridge view, try Mrs Macquaries Point, Blues Point Reserve, Lower Bradfield Park, Hickson Road Reserve or the Opera House forecourt. If you want a guaranteed spot without camping out from the morning, book a ticketed vantage point (from about $65), a harbourside dinner or party, or a fireworks cruise."),
    ("Are the Sydney NYE fireworks free to watch?",
     "Yes. Many harbour foreshore vantage points are free and open on a first-come, first-served basis. Some places need a free ticket (for example the Opera House forecourt and some islands), and some are paid ticketed areas run by councils with guaranteed entry, food and toilets."),
    ("How much does a New Year's Eve cruise on Sydney Harbour cost?",
     "Prices on the harbour usually run from about $1,100 to $2,500+ per person for dinner cruises that cover both the 9pm and midnight fireworks. Packages normally include a multi-course meal or canapés, drinks and a DJ or entertainment. Smaller boats and early-release tickets tend to sell out first."),
    ("Where can I have dinner with a fireworks view in Sydney?",
     f"Harbourfront restaurants like Aria, Quay, Bennelong, Whalebridge, Catalina, The Fenwick and Sails on Lavender Bay all run NYE menus with fireworks views. Early sittings (about $320–$400pp) are much cheaper than late sittings. See our <a href=\"/new-years-eve-dinner-sydney/\">NYE dinners in Sydney</a> list."),
    ("What time should I arrive at a free vantage point?",
     "The most popular foreshore spots, such as Mrs Macquaries Point and Hickson Road, can reach capacity by mid-morning on 31 December. Lesser-known parks in Balmain, Birchgrove and the North Shore usually fill by mid-to-late afternoon. Once a site is full, entry closes."),
    ("Is there public transport on New Year's Eve in Sydney?",
     "Yes. Extra trains, buses and ferries run all evening and through the night, and many city roads close from the afternoon. Public transport is by far the easiest way in and out. Check transportnsw.info for the official NYE timetable and road closures closer to the date."),
    ("Can I bring alcohol to the Sydney fireworks?",
     "It depends on the location. Many foreshore vantage points are alcohol-free zones, some allow BYO, and others have licensed bars. Check the rules for your chosen spot before you go. Glass is usually banned at public vantage points."),
    ("What are the best family-friendly NYE options in Sydney?",
     "The 9pm Family Fireworks are made for kids. Family-friendly options include ticketed parks like Lower Bradfield Park, Blues Point and Dudley Page Reserve, Taronga Zoo's Platinum tier (ages 5+), early dinner sittings, and quieter harbourside parks in Balmain and the North Shore."),
    ("Is NYE in Sydney the official Sydney New Year's Eve website?",
     "No. NYE in Sydney is an independent guide and event directory. The official event is produced by the City of Sydney. We bring together official vantage-point information and bookable dinners, cruises and parties so you can plan the whole night in one place."),
    ("How do I list my New Year's Eve event on NYE in Sydney?",
     f"It's a one-off ${CONFIG['listing_price']} fee with no commission. Your event gets its own optimised page, a place in our directory and category pages, and a direct link to your booking page. <a href=\"/list-your-event/\">List your event here</a>."),
]


def faq_html(items):
    return "".join(f"<details><summary>{escape(q)}</summary><p>{a}</p></details>" for q, a in items)


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
        ],
    }


TIMELINE = [
    ("Morning", "Popular free foreshore vantage points open. The best spots fill by mid-morning."),
    ("Afternoon", "Road closures start around the CBD and harbour. Ticketed parks and venues open their gates."),
    ("Early evening", "Aerial displays and on-water entertainment begin across the harbour."),
    ("Around 8:30pm", "Calling Country and Welcome to Country ceremonies honour the Traditional Custodians of the harbour."),
    ("9:00pm", "Family Fireworks. Around 8–10 minutes of pyrotechnics, perfect for kids."),
    ("Around 9:15pm", "The Harbour of Light Parade: illuminated vessels sail the harbour."),
    ("Midnight", f"The Midnight Fireworks. Around 12 minutes launched from the Harbour Bridge, barges and rooftops to welcome {NY}."),
    ("After midnight", "Extra public transport runs to get the crowds home safely. Allow plenty of time."),
]


def timeline_html():
    return '<div class="timeline">' + "".join(
        f'<div class="tl"><b>{t}</b><p>{d}</p></div>' for t, d in TIMELINE
    ) + "</div>"


VANTAGE = [
    ("Mrs Macquaries Point", "Royal Botanic Garden", "Opera House + Bridge together", "free", "Iconic postcard view; one of the first to reach capacity"),
    ("Hickson Road Reserve", "The Rocks", "Right under the Bridge", "free", "Alcohol-free; fills very early"),
    ("Sydney Opera House Forecourt", "Bennelong Point", "Front row to the harbour", "free-t", "Free ticket released 10am, 26 December; bars on site"),
    ("Bennelong Lawn, Fleet Steps & Tarpeian Lawn", "Royal Botanic Garden", "Opera House & Bridge", "check", "Food & drink available; check entry conditions"),
    ("Lower Bradfield Park", "Milsons Point", "Directly beside the Bridge", "paid", "$65 ticketed, guaranteed entry, facilities"),
    ("Blues Point Reserve", "McMahons Point", "Bridge + Opera House lined up", "paid", "$65 ticketed, guaranteed entry"),
    ("Cremorne Point & Lavender Bay Parklands", "North Shore", "Harbour & city skyline", "check", "Managed by North Sydney Council"),
    ("Dudley Page Reserve", "Dover Heights", "Panoramic elevated skyline", "paid", "$65 adult / $30 child / $170 family"),
    ("Goat Island", "On the harbour", "Island, close to the Bridge", "free-t", "Free ticket + ferry pass required"),
    ("Clark Island & Shark Island", "On the harbour", "Island views east of the Bridge", "paid", "Ticketed + ferry; sell out early"),
    ("Cockatoo Island", "On the harbour", "Western harbour views", "paid", "Available to accommodation and camping guests"),
    ("Thornton Park, Illoura Reserve & Lookes Ave Reserve", "Balmain East", "Western view of the Bridge", "free", "Family-friendly; some allow BYO alcohol"),
    ("Birchgrove parks", "Birchgrove", "Western harbour", "free", "Quieter, local feel"),
    ("Pyrmont Bay Park & Darling Harbour", "Pyrmont", "City and Darling Harbour", "free", "Close to restaurants and transport"),
]
PILL = {
    "free": '<span class="pill free">Free</span>',
    "free-t": '<span class="pill free">Free · ticket</span>',
    "paid": '<span class="pill paid">Paid ticket</span>',
    "check": '<span class="pill af">Check entry</span>',
}


def vantage_table(rows=None):
    rows = rows or VANTAGE
    body = "".join(
        f"<tr><td><b>{n}</b></td><td>{a}</td><td>{v}</td><td>{PILL[t]}</td><td class='muted'>{note}</td></tr>"
        for n, a, v, t, note in rows
    )
    return f"""<div class="table-wrap"><table><thead><tr><th>Vantage point</th><th>Area</th><th>View</th><th>Entry</th><th>Good to know</th></tr></thead>
<tbody>{body}</tbody></table></div>"""


# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------
def page_home():
    featured = [e for e in EVENTS if e.get("featured")]
    rest = [e for e in EVENTS if not e.get("featured")]
    ordered = featured + rest
    n = len(EVENTS)
    body = f"""
<section class="hero"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap">
<span class="eyebrow">Thursday 31 December {Y} · Sydney Harbour</span>
<h1>Sydney New Year's Eve {Y}<br><span class="grad">fireworks, parties &amp; dinners</span></h1>
<p class="lead">The best NYE events in Sydney in one place: harbour cruises, fireworks dinners, rooftop parties and every vantage point. Compare, choose and book your night to welcome {NY}.</p>
{countdown()}
<p class="cd-note">until the Midnight Fireworks over Sydney Harbour</p>
<div class="cta-row"><a class="btn btn-primary" href="#directory">Browse {n}+ NYE events</a><a class="btn btn-ghost" href="/sydney-fireworks-vantage-points/">Free vantage points</a></div>
</div></section>

<div class="wrap"><div class="facts">
<div class="fact"><b>9:00pm</b><span>Family Fireworks, about 8–10 mins</span></div>
<div class="fact"><b>Midnight</b><span>Main fireworks, about 12 mins from the Harbour Bridge</span></div>
<div class="fact"><b>1M+</b><span>people watching around the harbour</span></div>
<div class="fact"><b>{n}+</b><span>bookable dinners, cruises, parties &amp; ticketed spots</span></div>
</div></div>

{directory(ordered, f"Every Sydney NYE {Y} event in one directory", "Filter by type, area or budget. Every listing shows what's included, which fireworks you'll see and a direct booking link.")}

{list_band()}

<section class="alt"><div class="wrap two">
<div><h2>Your NYE {Y} in Sydney, <span class="grad">hour by hour</span></h2>
<p class="muted">Timings are based on recent years and confirmed by the City of Sydney closer to the night. Use this to plan when to arrive, eat and move.</p>
<a class="btn btn-ghost" href="/plan-your-night/">Full planning guide →</a></div>
{timeline_html()}
</div></section>

<section><div class="wrap">
<div class="section-head"><h2>Best fireworks vantage points</h2><p>Free, free-but-ticketed and paid harbour spots to watch the Sydney fireworks, with what you need to know about each one.</p></div>
{vantage_table(VANTAGE[:8])}
<p style="text-align:center;margin-top:24px"><a class="btn btn-ghost" href="/sydney-fireworks-vantage-points/">See all vantage points →</a></p>
</div></section>

<section class="alt"><div class="wrap">
<div class="section-head"><h2>Find your kind of NYE</h2></div>
<div class="grid">
<div class="card"><h3><a href="/new-years-eve-dinner-sydney/">🍽️ NYE dinners with fireworks views</a></h3><p>From $110 pub banquets to $1,950 degustations at Aria and Bennelong.</p><a href="/new-years-eve-dinner-sydney/">Browse dinners →</a></div>
<div class="card"><h3><a href="/new-years-eve-cruises-sydney/">🛥️ Sydney Harbour NYE cruises</a></h3><p>See both fireworks shows up close, right on the water.</p><a href="/new-years-eve-cruises-sydney/">Browse cruises →</a></div>
<div class="card"><h3><a href="/new-years-eve-parties-sydney/">🎉 NYE parties &amp; rooftops</a></h3><p>Opera Bar, Luna Park, rooftop bars and the Bondi Beach party.</p><a href="/new-years-eve-parties-sydney/">Browse parties →</a></div>
<div class="card"><h3><a href="/family-new-years-eve-sydney/">👨‍👩‍👧 Family-friendly NYE</a></h3><p>9pm fireworks, ticketed parks, Taronga and early sittings.</p><a href="/family-new-years-eve-sydney/">Browse family events →</a></div>
</div></div></section>

<section id="faq"><div class="wrap">
<div class="section-head"><h2>Sydney New Year's Eve {Y}: FAQ</h2></div>
<div class="faq">{faq_html(FAQ)}</div>
</div></section>
"""
    return layout(
        "/",
        f"Sydney New Year's Eve {Y}: Fireworks, Events & Dinners | NYE in Sydney",
        f"Plan Sydney New Year's Eve {Y}: live countdown, fireworks times (9pm & midnight), the best vantage points and {n}+ bookable NYE dinners, harbour cruises and parties.",
        body,
        schema=[item_list(ordered, f"Sydney New Year's Eve {Y} events"), faq_schema(FAQ),
                {"@context": "https://schema.org", "@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/",
                 "logo": URL + "/favicon.svg", "email": CONFIG["contact_email"]}],
    )


CATEGORY_PAGES = [
    {
        "path": "/new-years-eve-dinner-sydney/",
        "filter": lambda e: "dining" in e["categories"] or "fine-dining" in e["categories"],
        "title": f"New Year's Eve Dinner Sydney {Y}: Restaurants with Fireworks Views",
        "h1": f"New Year's Eve dinners in Sydney {Y}",
        "desc": f"The best New Year's Eve dinners in Sydney {Y}: harbourside restaurants with fireworks views, NYE degustations, early sittings and set menus, with prices and booking links.",
        "intro": "A harbourside table is the most comfortable way to watch the fireworks: no camping out, no crowds, and a long dinner while you wait for midnight. Early sittings usually include the 9pm show and cost far less, while late sittings take you through to the midnight fireworks.",
        "tips": ["Book early. The best harbourfront tables sell out months ahead.", "Early sittings (about $300–$400pp) are the best-value way to get a harbour view.", "Ask whether your table is guaranteed a fireworks view or only the venue is.", "Allow extra travel time: road closures start in the afternoon."],
    },
    {
        "path": "/new-years-eve-cruises-sydney/",
        "filter": lambda e: "cruise" in e["categories"],
        "title": f"Sydney NYE Cruises {Y}: Harbour Fireworks Dinner Cruises",
        "h1": f"Sydney Harbour New Year's Eve cruises {Y}",
        "desc": f"Compare Sydney Harbour New Year's Eve cruises for {Y}: dinner cruises, glass boats and party catamarans that cover both the 9pm and midnight fireworks.",
        "intro": "Being on the water is the closest you can get to the fireworks barges. NYE cruises normally board in the late afternoon, include dinner and drinks, and stay out for both the 9pm and midnight displays. Boats have to take up positions in exclusion zones set by NSW Maritime, so the operator's licence and position matter.",
        "tips": ["Check where the vessel will sit for the midnight show.", "Compare boarding wharf and return times, as transport after midnight is busy.", "Smaller capacity means more deck space at midnight.", "Most NYE cruises are 18+. Check before booking for families."],
    },
    {
        "path": "/new-years-eve-parties-sydney/",
        "filter": lambda e: "party" in e["categories"] or "rooftop" in e["categories"],
        "title": f"Sydney NYE Parties {Y}: Best New Year's Eve Parties & Rooftops",
        "h1": f"The best New Year's Eve parties in Sydney {Y}",
        "desc": f"Sydney's best New Year's Eve parties for {Y}: Opera Bar, Luna Park, rooftop bars, clubs and the Bondi Beach party, with prices, inclusions and tickets.",
        "intro": "From the Opera House to Bondi Beach, these are the best NYE parties in Sydney. Some sit right on the harbour with a full view of the fireworks. Others are rooftops, clubs and pubs where midnight is just part of the night.",
        "tips": ["Many parties release tickets in tiers, so the first release is the cheapest.", "Check whether drinks are included or pay-as-you-go.", "Most parties are 18+ with ID checks.", "Look for 'guaranteed fireworks view' if the view matters to you."],
    },
    {
        "path": "/family-new-years-eve-sydney/",
        "filter": lambda e: "family" in e["categories"] or "vantage" in e["categories"],
        "title": f"Family New Year's Eve Sydney {Y}: Kid-Friendly NYE & 9pm Fireworks",
        "h1": f"Family-friendly New Year's Eve in Sydney {Y}",
        "desc": f"Kid-friendly ways to celebrate New Year's Eve {Y} in Sydney: 9pm Family Fireworks, ticketed parks, Taronga Zoo and family dinners.",
        "intro": "The 9pm Family Fireworks were designed for kids, so you can see a full harbour show and be home in bed before midnight. Ticketed parks give you guaranteed space, toilets and food, which makes a big difference with little ones.",
        "tips": ["Aim for the 9pm Family Fireworks with younger kids.", "Ticketed parks guarantee space and facilities, so you don't need to arrive at dawn.", "Pack hats, sunscreen, water, a picnic rug and ear protection for little ones.", "Agree on a meeting point in case anyone gets separated."],
    },
]


def page_category(c):
    events = [e for e in EVENTS if c["filter"](e)]
    events.sort(key=lambda e: (not e.get("featured"), e["price_from"] if e["price_from"] is not None else 1e9))
    tips = "".join(f"<li>{t}</li>" for t in c["tips"])
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Sydney</span><h1>{c['h1']}</h1>
<p class="lead">{c['intro']}</p>{countdown(mini=True)}</div></section>
<section style="padding-bottom:0"><div class="wrap two">
<div class="panel"><h2 style="font-size:1.5rem">Booking tips</h2><ul class="ticks">{tips}</ul></div>
<div><h2 style="font-size:1.5rem">{len(events)} options, compared</h2><p class="muted">Every listing shows a "from" price, what's included and which fireworks you'll see. Prices are per person and based on published packages, so always confirm the current price with the venue.</p>
<a class="btn btn-primary" href="/list-your-event/">Add your venue: ${CONFIG['listing_price']}</a></div>
</div></section>
{directory(events, c['h1'], 'Filter and sort to find your night.')}
{list_band()}"""
    return layout(
        c["path"], c["title"] + " | NYE in Sydney", c["desc"], body,
        schema=[item_list(events, c["h1"]), breadcrumbs(("Home", "/"), (c["h1"], c["path"]))],
    )


def page_event(e):
    path = f"/events/{e['slug']}/"
    inc = "".join(f"<li>{escape(x)}</li>" for x in e["includes"])
    cats = ", ".join(CATEGORY_LABELS.get(c, c) for c in e["categories"])
    related = [x for x in EVENTS if x["slug"] != e["slug"] and (x["area"] == e["area"] or set(x["categories"]) & set(e["categories"]))][:3]
    offer = {"@type": "Offer", "url": e["url"], "priceCurrency": "AUD", "availability": "https://schema.org/InStock",
             "validFrom": f"{Y}-01-01"}
    if e["price_from"] is not None:
        offer["price"] = e["price_from"]
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"{e['name']} – New Year's Eve {Y}",
        "description": e["blurb"] + " Includes: " + "; ".join(e["includes"]) + ".",
        "startDate": f"{Y}-12-31",
        "endDate": f"{NY}-01-01",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": [f"{URL}/og.png"],
        "location": {
            "@type": "Place", "name": e["venue"],
            "address": {"@type": "PostalAddress", "addressLocality": e["suburb"], "addressRegion": "NSW", "addressCountry": "AU"},
        },
        "organizer": {"@type": "Organization", "name": e["venue"].split(",")[0], "url": e["url"]},
        "offers": offer,
    }
    body = f"""
<section class="event-hero"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/#directory">NYE events</a> › {escape(e['name'])}</nav>
<span class="eyebrow">New Year's Eve {Y} · {escape(e['suburb'])}</span>
<h1 style="font-size:clamp(2rem,5vw,3.4rem)">{escape(e['name'])}</h1>
<p class="lead muted" style="font-size:1.15rem;max-width:760px">{escape(e['blurb'])}</p>
</div></section>
<section style="padding-top:10px"><div class="wrap event-layout">
<div>
<div class="panel"><h2 style="font-size:1.5rem">What's included</h2><ul class="ticks">{inc}</ul></div>
<div class="prose" style="margin-top:30px">
<h2 style="font-size:1.5rem">About {escape(e['name'])}</h2>
<p>{escape(e['name'])} is at {escape(e['venue'])} in {escape(e['suburb'])} ({escape(e['area'])}). It's one of the {escape(cats.lower())} options for New Year's Eve {Y} in Sydney. Fireworks: <b>{escape(e['fireworks'])}</b>. Age: <b>{escape(e['age'])}</b>.</p>
<p>Planning the rest of your night? Check the <a href="/plan-your-night/">fireworks timeline and transport tips</a> or compare <a href="/sydney-fireworks-vantage-points/">vantage points around the harbour</a>.</p>
<p class="notice">Details are based on the venue's published NYE information and can change. Confirm the price, times and inclusions with {escape(e['venue'].split(',')[0])} before booking. Are you the venue? <a href="/list-your-event/">Claim and upgrade this listing</a>.</p>
</div></div>
<aside class="side panel">
<div class="price" style="font-size:2rem">{"Free" if e['price_from']==0 else money(e['price_from']) if e['price_from'] else "TBA"}<small>{escape(e['price_text'])}</small></div>
<dl><dt>Date</dt><dd>Thursday 31 December {Y}</dd><dt>Time</dt><dd>{escape(e['time'])}</dd>
<dt>Where</dt><dd>{escape(e['venue'])}</dd><dt>Fireworks</dt><dd>🎆 {escape(e['fireworks'])}</dd><dt>Age</dt><dd>{escape(e['age'])}</dd></dl>
<a class="btn btn-primary" style="width:100%;justify-content:center" href="{e['url']}" target="_blank" rel="noopener sponsored">Book with the venue →</a>
<div style="margin-top:20px">{countdown(mini=True)}</div>
</aside>
</div></section>
<section class="alt"><div class="wrap"><div class="section-head"><h2>You might also like</h2></div>
<div class="grid">{''.join(card(x, i) for i, x in enumerate(related))}</div></div></section>
{list_band()}"""
    return layout(
        path,
        (f"{e['name']} {Y}" if "NYE" in e["name"] or "New Year" in e["name"] else f"{e['name']} NYE {Y}")
        + f" – {e['suburb']} | NYE in Sydney",
        f"{e['name']} New Year's Eve {Y} in {e['suburb']}: {e['price_text']}. {e['blurb']}"[:300],
        body, og_type="article", active="/#directory",
        schema=[schema, breadcrumbs(("Home", "/"), ("NYE events", "/#directory"), (e["name"], path))],
    )


def page_vantage():
    vp = [e for e in EVENTS if "vantage" in e["categories"]]
    faq = FAQ[1:3] + FAQ[5:6] + FAQ[7:8]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Free &amp; ticketed</span>
<h1>Sydney fireworks vantage points {Y}</h1>
<p class="lead">Where to watch the Sydney New Year's Eve fireworks: free foreshore parks, free-ticketed islands and paid spots with guaranteed entry. Includes which ones fill first.</p></div></section>
<section><div class="wrap">
<div class="section-head"><h2>Vantage points at a glance</h2><p>Capacity and entry conditions are set by the City of Sydney, NSW Government and local councils each year. Check official updates on the day, as sites close once they're full.</p></div>
{vantage_table()}
</div></section>
{directory(vp, "Book a guaranteed spot", "Ticketed vantage points mean no dawn queue. Tickets usually release from September to December.", show_filters=False)}
<section class="alt"><div class="wrap prose">
<h2>How to choose a vantage point</h2>
<p><b>For the classic shot</b> with the Opera House and Harbour Bridge together, look west from Mrs Macquaries Point or east from Blues Point and McMahons Point.</p>
<p><b>To be close to the Bridge</b>, go for Hickson Road Reserve, Lower Bradfield Park or Luna Park. The midnight show launches straight off the Bridge.</p>
<p><b>For space and a quieter night</b>, try the Balmain East and Birchgrove parks, the islands (ferry plus ticket), or elevated eastern spots like Dudley Page Reserve.</p>
<p><b>With kids</b>, a ticketed park gives you guaranteed space, toilets and food. Make the 9pm Family Fireworks your main event.</p>
<h2>What to bring</h2>
<ul><li>Picnic rug and low chair (check whether chairs are allowed)</li><li>Water, snacks and sunscreen. You may be outdoors for 10+ hours</li><li>Charged phone and a power bank</li><li>A light jacket for after dark</li><li>No glass. Check the alcohol rules for your site</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Vantage point FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/sydney-fireworks-vantage-points/",
        f"Sydney NYE Fireworks Vantage Points {Y}: Best Free & Ticketed Spots | NYE in Sydney",
        f"The best places to watch the Sydney New Year's Eve fireworks in {Y}: free harbour vantage points, free-ticketed islands and $65 ticketed parks, plus what time to arrive.",
        body, schema=[faq_schema(faq), item_list(vp, "Ticketed vantage points"),
                      breadcrumbs(("Home", "/"), ("Vantage points", "/sydney-fireworks-vantage-points/"))],
    )


def page_plan():
    faq = [FAQ[0], FAQ[6], FAQ[7], FAQ[8]]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">Planning guide</span>
<h1>Plan your Sydney NYE {Y}</h1>
<p class="lead">Fireworks times, the run sheet for the night, getting there by public transport, road closures, accessibility and what to bring.</p>
{countdown(mini=True)}</div></section>
<section><div class="wrap two" style="align-items:start">
<div><h2>Fireworks times &amp; the night's schedule</h2><p class="muted">Times are based on recent years. The City of Sydney publishes the final {Y} program in December.</p></div>
{timeline_html()}
</div></section>
<section class="alt" id="transport"><div class="wrap prose">
<h2>Getting there: public transport</h2>
<p>Public transport is the best way to get to and from the harbour on New Year's Eve. Extra trains, buses, ferries and light rail run through the evening and all night. Stations near the harbour, especially Circular Quay, Wynyard and Milsons Point, get extremely busy and may close temporarily or run one-way to manage crowds.</p>
<ul><li>Plan your trip on <a href="https://transportnsw.info" rel="noopener" target="_blank">transportnsw.info</a> and check the special NYE timetable.</li>
<li>Have a back-up station in mind. Walking 10–15 minutes to a less busy station often saves an hour.</li>
<li>After midnight, expect queues. Stay for a drink or snack and leave once the first wave has gone.</li></ul>
<h2 id="roads">Road closures &amp; driving</h2>
<p>Big parts of the CBD, The Rocks, North Sydney and roads around the Harbour Bridge close from the afternoon of 31 December until the early hours of 1 January. Parking near the harbour is close to impossible. If you have to drive, park well outside the closure zone and finish the trip by public transport.</p>
<h2 id="boating">Boating on the harbour</h2>
<p>Private boats must follow NSW Maritime exclusion zones and NYE rules, and the harbour is very busy. For most people a licensed <a href="/new-years-eve-cruises-sydney/">NYE cruise</a> is the easiest way to see the show from the water.</p>
<h2 id="accessibility">Accessibility</h2>
<p>Several vantage points have accessible viewing areas, accessible toilets and companion access. These spaces are limited, so plan ahead and check the official accessibility information for your site. Many of the harbourside venues in our directory have step-free access. Contact the venue to confirm.</p>
<h2>Safety &amp; wellbeing</h2>
<ul><li>Drink plenty of water. It's usually a hot day and a long night.</li><li>Agree on a meeting point with your group.</li><li>Follow police and staff directions. Sites close when full.</li><li>Look after your mates, and get help from first-aid stations if you need it.</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Planning FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/plan-your-night/",
        f"Sydney NYE {Y} Fireworks Times, Transport & Planning Guide | NYE in Sydney",
        f"Sydney New Year's Eve {Y} planning guide: 9pm and midnight fireworks times, the schedule for the night, public transport, road closures, accessibility and what to bring.",
        body, schema=[faq_schema(faq), breadcrumbs(("Home", "/"), ("Plan your night", "/plan-your-night/"))],
    )


def page_list():
    p = CONFIG["listing_price"]
    cats = "".join(f'<option value="{k}">{v}</option>' for k, v in CATEGORY_LABELS.items() if k not in ("budget", "free"))
    faq = [
        ("What do I get for $" + str(p) + "?", "A dedicated event page built for search, with Google Event structured data. You also get a listing in our main directory and the matching category pages (dinners, cruises, parties, family), a direct link to your own booking page, and edits until 31 December."),
        ("Do you take commission on bookings?", "No. Guests book directly with you through your own link, and you keep 100% of every ticket."),
        ("How long does my listing stay live?", f"Your listing stays live until New Year's Day {NY}, then rolls into our archive. Previous listers get first right to renew for next year."),
        ("How fast will my listing go live?", "Usually within one business day of payment. We'll email you the link."),
        ("Can I update prices or details?", "Yes. Email us any changes (sold-out tiers, price releases, new acts) and we'll update your page."),
    ]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">For venues, promoters &amp; cruise operators</span>
<h1>List your New Year's Eve event</h1>
<p class="lead">Put your NYE {Y} event in front of people searching for "New Year's Eve Sydney", "NYE dinner Sydney" and "NYE cruise Sydney" in the weeks they're deciding where to go.</p>
{countdown(mini=True)}</div></section>
<section><div class="wrap two" style="align-items:start">
<div>
<h2>Why list with <span class="grad">NYE in Sydney</span>?</h2>
<ul class="ticks">
<li><b>High-intent visitors.</b> People only visit a NYE guide when they're about to book.</li>
<li><b>Your own SEO page.</b> Each event gets a dedicated page with Google Event schema, which can make it eligible for event rich results.</li>
<li><b>Listed where people browse.</b> You appear in the main directory plus every matching category: dinners, cruises, parties and family.</li>
<li><b>Zero commission.</b> Guests click straight through to your booking page.</li>
<li><b>Updates until NYE.</b> Change prices, add tiers or mark sold-out tiers whenever you like.</li>
<li><b>Countdown traffic.</b> Interest peaks from October to 31 December, right when you're selling.</li>
</ul>
</div>
<div class="pricing">
<span class="eyebrow">NYE {Y} listing</span>
<div class="amount"><sup>$</sup>{p}</div>
<p class="muted">AUD inc GST · one-off · no commission</p>
<ul class="ticks">
<li>Dedicated event page + Google Event schema</li>
<li>Directory &amp; category page placement</li>
<li>Direct "Book" button to your site</li>
<li>Unlimited edits until 31 Dec {Y}</li>
<li>Live within 1 business day</li>
</ul>
<a class="btn btn-primary" href="#form" style="width:100%;justify-content:center">List my event →</a>
</div>
</div></section>
<section class="alt" id="form"><div class="wrap" style="max-width:860px">
<div class="section-head"><h2>Your event details</h2><p>Fill this in, then pay ${p} securely. We'll publish your page and email you the link.</p></div>
<form class="listing panel" data-endpoint="{CONFIG['form_endpoint']}" data-payment="{CONFIG['payment_link']}" data-email="{CONFIG['contact_email']}">
<div><label for="f-name">Event name *</label><input id="f-name" name="event_name" required></div>
<div><label for="f-venue">Venue *</label><input id="f-venue" name="venue" required></div>
<div><label for="f-suburb">Suburb *</label><input id="f-suburb" name="suburb" required></div>
<div><label for="f-cat">Type *</label><select id="f-cat" name="category" required>{cats}</select></div>
<div><label for="f-price">Price from (AUD pp)</label><input id="f-price" name="price_from" inputmode="decimal" placeholder="e.g. 249"></div>
<div><label for="f-time">Times</label><input id="f-time" name="times" placeholder="e.g. 7pm – 1am"></div>
<div><label for="f-fw">Fireworks view</label><select id="f-fw" name="fireworks"><option>Both 9pm &amp; midnight</option><option>Midnight only</option><option>9pm only</option><option>Partial / nearby</option><option>No view</option></select></div>
<div><label for="f-age">Age</label><select id="f-age" name="age"><option>18+</option><option>All ages</option><option>Family-friendly</option></select></div>
<div class="full"><label for="f-url">Booking URL *</label><input id="f-url" name="booking_url" type="url" required placeholder="https://"></div>
<div class="full"><label for="f-desc">Description &amp; inclusions *</label><textarea id="f-desc" name="description" required placeholder="What makes your night special? Food, drinks, DJs, views…"></textarea></div>
<div><label for="f-contact">Contact name *</label><input id="f-contact" name="contact_name" required></div>
<div><label for="f-email">Email *</label><input id="f-email" name="email" type="email" required></div>
<div><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel"></div>
<div><label for="f-abn">Business / ABN</label><input id="f-abn" name="business"></div>
<input type="hidden" name="_subject" value="New NYE listing request">
<div class="full"><button class="btn btn-primary" type="submit">Continue to payment: ${p} →</button>
<p class="form-status muted" aria-live="polite" style="margin:12px 0 0"></p></div>
</form>
</div></section>
<section><div class="wrap"><div class="section-head"><h2>Listing FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>"""
    service = {
        "@context": "https://schema.org", "@type": "Service", "name": f"NYE {Y} event listing",
        "provider": {"@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/"},
        "areaServed": "Sydney, NSW",
        "offers": {"@type": "Offer", "price": p, "priceCurrency": "AUD", "url": URL + "/list-your-event/"},
    }
    return layout(
        "/list-your-event/",
        f"List Your New Year's Eve Event in Sydney – ${p} | NYE in Sydney",
        f"Promote your Sydney New Year's Eve {Y} party, dinner or cruise. ${p} flat fee, no commission: a dedicated SEO event page, directory placement and a direct booking link.",
        body, schema=[service, faq_schema(faq), breadcrumbs(("Home", "/"), ("List your event", "/list-your-event/"))],
    )


def page_404():
    body = f"""<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}<div class="wrap">
<h1>This page fizzled out</h1><p class="lead">The page you're after isn't here, but the fireworks still are.</p>{countdown()}
<div class="cta-row"><a class="btn btn-primary" href="/">Back to all NYE events</a></div></div></section>"""
    return layout("/404.html", "Page not found | NYE in Sydney", "Page not found.", body).replace(
        'content="index,follow', 'content="noindex,follow')


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#07061a"/><g stroke-linecap="round" stroke-width="4"><path d="M32 32 32 8" stroke="#ffc94d"/><path d="M32 32 53 20" stroke="#ff4fa3"/><path d="M32 32 53 44" stroke="#8b5cff"/><path d="M32 32 32 56" stroke="#41e3ff"/><path d="M32 32 11 44" stroke="#ffc94d"/><path d="M32 32 11 20" stroke="#ff4fa3"/></g><circle cx="32" cy="32" r="5" fill="#fff"/></svg>"""

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700&family=Playfair+Display:wght@800&display=swap" rel="stylesheet">
<style>body{{margin:0;width:1200px;height:630px;background:radial-gradient(ellipse at 50% 120%,#2a1a6b,transparent 60%),radial-gradient(ellipse at 85% 0%,#3a0f4d,transparent 55%),#07061a;color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.t{{position:absolute;left:70px;top:90px;right:70px}}h1{{font-family:'Playfair Display',serif;font-size:96px;margin:0;line-height:1}}
.g{{background:linear-gradient(120deg,#ffc94d,#ff4fa3 50%,#8b5cff);-webkit-background-clip:text;color:transparent}}
p{{font-size:34px;color:#cfc9ff;margin:24px 0 0}}.b{{display:inline-block;margin-top:30px;padding:12px 26px;border-radius:99px;background:linear-gradient(120deg,#ffc94d,#ff4fa3);color:#14062b;font-weight:700;font-size:26px}}
.s{{position:absolute;bottom:0;left:0;width:100%}}.dot{{position:absolute;border-radius:50%}}</style></head><body>
<div class="t"><h1>NYE <span class="g">in Sydney</span></h1><p>Fireworks · Cruises · Dinners · Parties<br>New Year's Eve {Y} on Sydney Harbour</p><span class="b">Countdown to {NY} →</span></div>
{SKYLINE.replace('class="skyline"', 'class="s"')}
<script>for(let k=0;k<4;k++){{const cx=830+k*95,cy=90+(k%2)*110,c=['#ffc94d','#ff4fa3','#8b5cff','#41e3ff'][k];for(let i=0;i<48;i++){{const a=i/48*6.283,r=30+Math.random()*40,d=document.createElement('div');d.className='dot';d.style.cssText=`left:${{cx+Math.cos(a)*r}}px;top:${{cy+Math.sin(a)*r}}px;width:4px;height:4px;background:${{c}};box-shadow:0 0 8px ${{c}}`;document.body.appendChild(d)}}}}</script>
</body></html>"""


def build():
    if OUT.exists():
        og_keep = (OUT / "og.png").read_bytes() if (OUT / "og.png").exists() else None
        shutil.rmtree(OUT)
    else:
        og_keep = None
    OUT.mkdir()
    pages = {"/": page_home(), "/sydney-fireworks-vantage-points/": page_vantage(),
             "/plan-your-night/": page_plan(), "/list-your-event/": page_list()}
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
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / "og.html").write_text(OG_HTML)
    if og_keep:
        (OUT / "og.png").write_bytes(og_keep)
    (OUT / ".nojekyll").write_text("")
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
