import re
#!/usr/bin/env python3
"""
BOV Website Builder Template — LAAA Team at Marcus & Millichap
==============================================================
This is a TEMPLATE. All placeholders marked # DEAL-SPECIFIC must be
replaced with actual property data before running.

Usage:
  1. Copy this file to C:/Users/gscher/{slug}-bov/build_bov.py
  2. Replace ALL # DEAL-SPECIFIC placeholders
  3. Copy images to {slug}-bov/images/
  4. Run: python build_bov.py
  5. Output: index.html
"""
import base64, json, os, sys, io, math, urllib.request, urllib.parse, statistics

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
OUTPUT = os.path.join(SCRIPT_DIR, "index.html")

# ============================================================
# DEAL-SPECIFIC CONFIG — Replace these for every build
# ============================================================
SLUG = "124oceano"
ADDRESS = "124 Oceano Ave"
CITY_STATE_ZIP = "Santa Barbara, CA 93109"
FULL_ADDRESS = "124 Oceano Ave, Santa Barbara, CA 93109"
SUBMARKET = "The Mesa"
CLIENT_NAME = "Oceano Enterprises LLC"
COVER_MONTH_YEAR = "June 2026"
PROPERTY_SUBTITLE = "Fully Renovated 7-Unit Coastal Multifamily | Delivered Vacant"

# Aerial View flyover (Google) — videoId rendered 2026-06-11; the page fetches a fresh
# stream URI on every load per Google's no-caching policy. Key below is the same public
# browser key laaa.com already ships in its client bundles (NEXT_PUBLIC_GOOGLE_MAPS_KEY).
AERIAL_VIDEO_ID = "tRP8AKt1GNwweR-EiW4fNA"
MAPS_BROWSER_KEY = "AIzaSyB1FbBfb4q0FVpiMSHBhjERp_R2lP3wDE8"

BOV_BASE_URL = f"https://{SLUG}.laaa.com"
PDF_WORKER_URL = "https://laaa-pdf-worker.laaa-team.workers.dev"
PDF_FILENAME = f"BOV - {FULL_ADDRESS}.pdf"  # DEAL-SPECIFIC
PDF_LINK = (PDF_WORKER_URL + "/?url=" + urllib.parse.quote(BOV_BASE_URL + "/", safe="")
            + "&filename=" + urllib.parse.quote(PDF_FILENAME, safe=""))

# Section inclusion flags — set per deal
INCLUDE_TRANSACTION_HISTORY = False
INCLUDE_DEVELOPMENT_POTENTIAL = False
INCLUDE_ADU_OPPORTUNITY = False
INCLUDE_ON_MARKET_COMPS = True  # 160 Ash Ave active competition (Glen-directed 2026-06-11); table + narrative only, no map (Carpinteria sits far out of the same-street frame)
INCLUDE_RENOVATION = True  # custom section for this build (gut-reno, delivered vacant)
PROPERTY_TYPE = "stabilized"  # pro forma stabilized presentation (delivered vacant)

# Agent lineup — Logan Ward lead + Glen + Filip (verbatim from team_contacts.md)
COVER_AGENTS = [
    {"name": "Logan Ward", "title": "Associate", "img_key": "team_logan"},
    {"name": "Glen Scher", "title": "Senior Managing Director Investments", "img_key": "glen"},
    {"name": "Filip Niculete", "title": "Senior Managing Director Investments", "img_key": "filip"},
]
FOOTER_AGENTS = [
    {
        "name": "Logan Ward",
        "title": "Associate",
        "phone": "(818) 212-2675",
        "email": "Logan.Ward@marcusmillichap.com",
        "license": "02200464",
        "img_key": "team_logan",
    },
    {
        "name": "Glen Scher",
        "title": "Senior Managing Director Investments",
        "phone": "(818) 212-2808",
        "email": "Glen.Scher@marcusmillichap.com",
        "license": "01962976",
        "img_key": "glen",
    },
    {
        "name": "Filip Niculete",
        "title": "Senior Managing Director Investments",
        "phone": "(818) 212-2748",
        "email": "Filip.Niculete@marcusmillichap.com",
        "license": "01905352",
        "img_key": "filip",
    },
]

# ============================================================
# IMAGE LOADING
# ============================================================
def load_image_b64(filename):
    path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(path):
        print(f"WARNING: Image not found: {path}")
        return ""
    ext = filename.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp"}.get(ext, "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    print(f"  Loaded: {filename} ({len(data)//1024}KB)")
    return f"data:{mime};base64,{data}"

print("Loading images...")
IMG = {
    # Standard branding (same for every BOV — copy from LAAA-AI-Prompts/branding/)
    "logo": load_image_b64("LAAA_Team_White.png"),
    "logo_blue": load_image_b64("LAAA_Team_Blue.png"),
    "closings_map": load_image_b64("closings-map.png"),
    # Team headshots (copy from LAAA-AI-Prompts/branding/headshots/)
    "glen": load_image_b64("Glen_Scher.png"),
    "filip": load_image_b64("Filip_Niculete.png"),
    "team_aida": load_image_b64("Aida_Memary_Scher.png"),
    "team_morgan": load_image_b64("Morgan_Wetmore.png"),
    "team_luka": load_image_b64("Luka_Leader.png"),
    "team_logan": load_image_b64("Logan_Ward.png"),
    "team_alexandro": load_image_b64("Alexandro_Tapia.png"),
    "team_blake": load_image_b64("Blake_Lewitt.png"),
    "team_mike": load_image_b64("Mike_Palade.png"),
    "team_tony": load_image_b64("Tony_Dang.png"),
    # Deal-specific photos
    "hero": load_image_b64("hero.jpg"),          # Leadbetter aerial w/ parcel outline (poster + print)
    "grid1": load_image_b64("grid1.jpg"),        # renovated living room (slider/patio)
    "buyer_photo": load_image_b64("buyer_photo.jpg"),  # renovated dining/living
    "reno_ext": load_image_b64("reno_ext.jpg"),  # building exterior "124"
    "reno_bed": load_image_b64("reno_bed.jpg"),  # renovated bedroom
    "reno_bed2": load_image_b64("reno_bed2.jpg"),# renovated bedroom 2
    "reno_room": load_image_b64("reno_room.jpg"),# renovated room w/ hall
    "floorplan": load_image_b64("floor-plan-2bd2ba.png"),  # Hover scan 2025-08-20, representative 2BD/2BA
}

# ============================================================
# GEOCODING — US Census Bureau Geocoder
# ============================================================
def geocode_census(addr):
    url = (f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
           f"?address={urllib.parse.quote(addr)}&benchmark=Public_AR_Current&format=json")
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        m = data["result"]["addressMatches"]
        if not m:
            print(f"  WARNING: No match for: {addr}")
            return None
        lat, lng = m[0]["coordinates"]["y"], m[0]["coordinates"]["x"]
        print(f"  Geocoded: {addr} -> ({lat:.6f}, {lng:.6f})")
        return (lat, lng)
    except Exception as e:
        print(f"  WARNING: Geocode failed for {addr}: {e}")
        return None

# Coordinates resolved 2026-06-11 via laaa-geo resolveAddress() (Places API New, all ROOFTOP).
# Sanctioned source per coordinate rule. place_ids persisted in Claude's BOV Workspace/geo_pins.json.
print("\nUsing resolved rooftop pins (laaa-geo resolveAddress, 2026-06-11)...")
SUBJECT_ADDR = FULL_ADDRESS
SUBJECT_COORDS = (34.4026428, -119.7025619)  # place_id ChIJqXIlhAwU6YAR2X-LsJOLjHs
SUBJECT_LAT, SUBJECT_LNG = SUBJECT_COORDS
SUBJECT_PLACE_ID = "ChIJqXIlhAwU6YAR2X-LsJOLjHs"

COMP_ADDRESSES = {
    "Sea Cliff Apartments, 20-80 Oceano Ave, Santa Barbara, CA 93109": (34.4018736, -119.7014270),  # ChIJ37TYjwsU6YAR8od-MaXjd3Q
    "330 Oceano Ave, Santa Barbara, CA 93109": (34.4042084, -119.7050692),  # ChIJMToZ1XIU6YARpomVC1DLJhg
}
RENT_COMP_ADDRESSES = {
    "Sea Crest Apartments, 100 Oceano Ave, Santa Barbara, CA 93109": (34.4022801, -119.7021100),  # ChIJ_7F6gAsU6YARq_4uJ-iNTCs
    "868 Highland Dr, Santa Barbara, CA 93109": (34.4101563, -119.7114878),  # ChIJl0UqHW8U6YARge3gOYSzWUs
    "1021 Cliff Dr, Santa Barbara, CA 93109": (34.4039270, -119.7054692),  # ChIJI-QaLQ0U6YARrFlK0_fsMpg
    "Sea Cliff Apartments, 20-80 Oceano Ave, Santa Barbara, CA 93109 (rent)": (34.4018736, -119.7014270),
}

# ============================================================
# STATIC MAP GENERATION (Pillow + OSM Tiles)
# ============================================================
from PIL import Image, ImageDraw, ImageFont

def lat_lng_to_tile(lat, lng, zoom):
    n = 2 ** zoom
    x = int((lng + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y

def _load_server_maps_key():
    """Build-time only: Google Static Maps key from credentials env. Never shipped in HTML."""
    cred_path = r"C:\Users\gscher\.claude\scripts\.credentials.env"
    try:
        with open(cred_path) as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_SERVER_KEY="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return None

_GMAPS_SERVER_KEY = _load_server_maps_key()

def generate_static_map(center_lat, center_lng, markers, width=800, height=400, zoom=14):
    """Google Static Maps (hard rule: Google Maps only). Output is a base64 PNG baked
    into the page at build time, so the server key never ships."""
    if not _GMAPS_SERVER_KEY:
        print("  WARNING: no Google Maps server key; static map skipped")
        return ""
    scale = 2
    params = [
        ("center", f"{center_lat},{center_lng}"),
        ("zoom", str(zoom)),
        ("size", f"{min(width, 640)}x{min(height, 640)}"),
        ("scale", str(scale)),
        ("maptype", "roadmap"),
        ("key", _GMAPS_SERVER_KEY),
    ]
    for m in markers:
        color = m.get("color", "#1B3A5C").replace("#", "0x")
        label = m.get("label", "")
        if label == "★":
            params.append(("markers", f"color:0xC5A258|size:mid|{m['lat']},{m['lng']}"))
        else:
            lbl = f"label:{label}|" if label and label.isalnum() else ""
            params.append(("markers", f"color:{color}|{lbl}{m['lat']},{m['lng']}"))
    url = "https://maps.googleapis.com/maps/api/staticmap?" + urllib.parse.urlencode(params)
    try:
        png = urllib.request.urlopen(url, timeout=30).read()
        img = Image.open(io.BytesIO(png)).convert("RGB")
        if img.width != width or img.height != height:
            ratio = max(width / img.width, height / img.height)
            img = img.resize((int(img.width * ratio) + 1, int(img.height * ratio) + 1))
            left = (img.width - width) // 2
            top = (img.height - height) // 2
            img = img.crop((left, top, left + width, top + height))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        print(f"  Google static map: {width}x{height}, {len(markers)} markers, {len(b64)//1024}KB")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"  WARNING: Google static map failed: {e}")
        return ""

def calc_auto_zoom(markers, width=800, height=300, padding_pct=0.10):
    if len(markers) <= 1:
        return 15
    lats = [m["lat"] for m in markers]
    lngs = [m["lng"] for m in markers]
    lat_span = max(lats) - min(lats)
    lng_span = max(lngs) - min(lngs)
    lat_span = max(lat_span * (1 + padding_pct * 2), 0.002)
    lng_span = max(lng_span * (1 + padding_pct * 2), 0.002)
    zoom_lat = math.log2(height / 256 * 360 / lat_span) if lat_span > 0 else 18
    zoom_lng = math.log2(width / 256 * 360 / lng_span) if lng_span > 0 else 18
    zoom = int(min(zoom_lat, zoom_lng))
    return max(10, min(zoom, 16))

def build_markers_from_comps(comps, addr_dict, comp_color, subject_lat, subject_lng):
    """Build map markers. Tier 1-2 comps get full color, Tier 3 gets muted gray."""
    markers = [{"lat": subject_lat, "lng": subject_lng, "label": "★", "color": "#C5A258"}]
    tier3_color = "#9E9E9E"  # Muted gray for Tier 3 / reference comps
    for i, c in enumerate(comps):
        for a, coords in addr_dict.items():
            if coords and c["addr"].lower() in a.lower():
                color = tier3_color if c.get("tier", 1) == 3 else comp_color
                markers.append({"lat": coords[0], "lng": coords[1], "label": str(i + 1), "color": color})
                break
    return markers

# ============================================================
# FINANCIAL CONSTANTS — DEAL-SPECIFIC (replace ALL)
# ============================================================
LIST_PRICE = 4_995_000
UNITS = 7
SF = 5175  # BLEND: 5 typical 2BD/2BA at ~720 SF gross (Hover interior scan 2025-08-20, 638 SF
# interior + walls, see 00_Source_Extractions/hover_floor_plan_extraction.md) + Unit 1 ~900 SF
# (owner plan, unconfirmed) + Unit 3 ~675 SF (1BD estimate). Assessor blank; flagged in disclaimer.
LOT_SF = 9147
LOT_ACRES = 0.21
YEAR_BUILT = "c. 1965"  # ESTIMATE — county publishes no year built for this parcel; anchored to
# comparable Oceano Ave multifamily vintages (330 Oceano built 1965; 101 Oceano condos 1961).
# Displayed with "(Est.)" labeling everywhere; renovation year 2026 shown separately.
TAX_RATE = 0.0105404  # Santa Barbara TRA 002-001 ad valorem (verified from 2025 bill)
FIXED_ASSESSMENTS = 69.99  # SB flat direct assessments (flood + vector), price-independent
GSR = 348_840  # pro forma: 5 x $4,295 + 1 x $4,395 + 1 x $3,200, x12 (delivered vacant)
PF_GSR = 348_840  # same — building delivers at pro forma
VACANCY_PCT = 0.03  # Glen-directed
OTHER_INCOME = 2_000  # laundry + storage (Glen-directed $1,500-$2,000)
NON_TAX_CUR_EXP = 47_192  # Rev 2 stack: ins 12,000 + W/S 5,200 + trash 2,450 + CAE 1,500 + R&M 4,200 + contract 1,750 + admin 1,000 + mgmt 17,442 (5% GSR) + reserves 1,400 + misc 250
NON_TAX_PF_EXP = 47_192

# Financing — interest_rate_engine.md run 2026-06-11: 5-Yr UST 4.18% (Treasury.gov) + 200 bps
# bank spread (renovated-condition credit offsets SB location and loan-size bumps), rounded down
INTEREST_RATE = 0.0615
AMORTIZATION_YEARS = 30
MAX_LTV = 0.55
MIN_DCR = 1.25

# Trade range (Glen-approved)
TRADE_RANGE_LOW = 4_750_000
TRADE_RANGE_HIGH = 4_995_000

# ============================================================
# FINANCIAL HELPER FUNCTIONS
# ============================================================
def calc_loan_constant(rate, amort):
    r = rate / 12
    n = amort * 12
    monthly = r * (1 + r)**n / ((1 + r)**n - 1)
    return monthly * 12

LOAN_CONSTANT = calc_loan_constant(INTEREST_RATE, AMORTIZATION_YEARS)

def calc_principal_reduction_yr1(loan_amount, annual_rate, amort_years):
    r = annual_rate / 12
    n = amort_years * 12
    monthly_pmt = loan_amount * (r * (1 + r)**n) / ((1 + r)**n - 1)
    balance = loan_amount
    total_principal = 0
    for _ in range(12):
        interest = balance * r
        principal = monthly_pmt - interest
        total_principal += principal
        balance -= principal
    return total_principal

def calc_metrics(price):
    taxes = price * TAX_RATE + FIXED_ASSESSMENTS  # SB: ad valorem + flat direct assessments
    cur_egi = GSR * (1 - VACANCY_PCT) + OTHER_INCOME
    pf_egi = PF_GSR * (1 - VACANCY_PCT) + OTHER_INCOME
    cur_exp = NON_TAX_CUR_EXP + taxes
    pf_exp = NON_TAX_PF_EXP + taxes
    cur_noi = cur_egi - cur_exp
    pf_noi = pf_egi - pf_exp
    ltv_max_loan = price * MAX_LTV
    dcr_max_loan = cur_noi / (MIN_DCR * LOAN_CONSTANT) if LOAN_CONSTANT > 0 else ltv_max_loan
    loan_amount = min(ltv_max_loan, dcr_max_loan)
    actual_ltv = loan_amount / price if price > 0 else 0
    loan_constraint = "LTV" if ltv_max_loan <= dcr_max_loan else "DCR"
    down_payment = price - loan_amount
    debt_service = loan_amount * LOAN_CONSTANT
    net_cf_cur = cur_noi - debt_service
    net_cf_pf = pf_noi - debt_service
    coc_cur = net_cf_cur / down_payment * 100 if down_payment > 0 else 0
    coc_pf = net_cf_pf / down_payment * 100 if down_payment > 0 else 0
    dcr_cur = cur_noi / debt_service if debt_service > 0 else 0
    dcr_pf = pf_noi / debt_service if debt_service > 0 else 0
    prin_red = calc_principal_reduction_yr1(loan_amount, INTEREST_RATE, AMORTIZATION_YEARS)
    return {
        "price": price, "taxes": taxes,
        "cur_noi": cur_noi, "pf_noi": pf_noi,
        "cur_egi": cur_egi, "pf_egi": pf_egi,
        "cur_exp": cur_exp, "pf_exp": pf_exp,
        "per_unit": price / UNITS if UNITS > 0 else 0,
        "per_sf": price / SF if SF > 0 else 0,
        "cur_cap": cur_noi / price * 100 if price > 0 else 0,
        "pf_cap": pf_noi / price * 100 if price > 0 else 0,
        "grm": price / GSR if GSR > 0 else 0,
        "pf_grm": price / PF_GSR if PF_GSR > 0 else 0,
        "loan_amount": loan_amount, "down_payment": down_payment,
        "actual_ltv": actual_ltv, "loan_constraint": loan_constraint,
        "debt_service": debt_service,
        "net_cf_cur": net_cf_cur, "net_cf_pf": net_cf_pf,
        "coc_cur": coc_cur, "coc_pf": coc_pf,
        "dcr_cur": dcr_cur, "dcr_pf": dcr_pf,
        "prin_red": prin_red,
        "total_return_pct_cur": (net_cf_cur + prin_red) / down_payment * 100 if down_payment > 0 else 0,
        "total_return_pct_pf": (net_cf_pf + prin_red) / down_payment * 100 if down_payment > 0 else 0,
    }

# ============================================================
# PRICING MATRIX
# ============================================================
# Dynamic increment: gap = LIST_PRICE - TRADE_RANGE_LOW
# min_inc = gap/4, max_inc = gap/3
# Pick smallest clean value in [min_inc, max_inc]: 25K, 50K, 75K, 100K, 150K, 200K, 250K
INCREMENT = 75_000  # DEAL-SPECIFIC — calculate per deal
MATRIX_PRICES = list(range(LIST_PRICE + 5 * INCREMENT, LIST_PRICE - 5 * INCREMENT - 1, -INCREMENT))
MATRIX = [calc_metrics(p) for p in MATRIX_PRICES]
AT_LIST = calc_metrics(LIST_PRICE)

if LIST_PRICE > 0:
    print(f"\nFinancials at list ${LIST_PRICE:,}: Cap {AT_LIST['cur_cap']:.2f}%, GRM {AT_LIST['grm']:.2f}x, NOI ${AT_LIST['cur_noi']:,.0f}")

# ============================================================
# DATA PLACEHOLDERS — DEAL-SPECIFIC (replace ALL)
# ============================================================

# Rent Roll — stabilized format: (unit, type, sf, rent, status, notes)
# Building delivered 100% vacant; rents are pro forma at delivery (Glen-set, comp-validated).
# Unit 3 = 1BD per Zillow building roster; unit numbering otherwise preliminary per owner plans.
# Typical 2BD/2BA SF = ~720 gross per Hover interior scan of one representative unit (2025-08-20):
# 638 SF interior room area plus walls. Which unit was scanned is unconfirmed (seller call 6/12).
RENT_ROLL = [
    ("1", "2BD/2BA", 900, 4395, "Delivered Vacant", "Larger plan (±900 SF, owner plan)"),
    ("2", "2BD/2BA", 720, 4295, "Delivered Vacant", "Typical plan (Hover-measured)"),
    ("3", "1BD/1BA", 675, 3200, "Delivered Vacant", "Pro forma at delivery"),
    ("4", "2BD/2BA", 720, 4295, "Delivered Vacant", "Typical plan (Hover-measured)"),
    ("5", "2BD/2BA", 720, 4295, "Delivered Vacant", "Typical plan (Hover-measured)"),
    ("6", "2BD/2BA", 720, 4295, "Delivered Vacant", "Typical plan (Hover-measured)"),
    ("7", "2BD/2BA", 720, 4295, "Delivered Vacant", "Typical plan (Hover-measured)"),
]

# Sale Comps
# Fields: num, addr, units, yr, sf, price, ppu, psf, cap, grm, date, dom, notes, tier, laaa
# - cap: verified cap rate (recalculated from NOI / sale price). Use "--" if NOI unavailable.
# - tier: 1 (primary), 2 (supporting), 3 (reference) — from COMP_ANALYSIS_PROTOCOL.md
# - laaa: True if Glen/Filip/LAAA Team sold this comp (gets gold badge in table)
# Same-street set per Glen 2026-06-11: Sea Cliff (oceanfront trophy) + 330 Oceano (unrenovated floor).
# Sea Cliff cap/GRM derived from its OM income at the $21.15M close; broker-stated basis noted in narrative.
SALE_COMPS = [
    {"num": 1, "addr": "Sea Cliff Apartments, 20-80 Oceano Ave", "units": 29, "yr": "--", "sf": 34865, "price": 21150000, "ppu": 729310, "psf": 607, "cap": 4.75, "grm": 11.9, "date": "02/2025", "dom": "--", "notes": "Oceanfront, same street", "tier": 1, "laaa": False},
    {"num": 2, "addr": "330 Oceano Ave", "units": 5, "yr": 1965, "sf": 4298, "price": 2950000, "ppu": 590000, "psf": 686, "cap": "--", "grm": "--", "date": "11/2024", "dom": "--", "notes": "Unrenovated, same street", "tier": 1, "laaa": False},
]

# On-Market Comps
# 160 Ash facts: 00_Source_Extractions/comp_160_ash_carpinteria.md. SF "--" on purpose: the
# published 7,405 figure conflicts between living area (gtprop) and lot size (aggregator).
# List price history: $6.5M 6/11/2025 -> $5.9M 7/31/2025 -> $5,495,000 9/26/2025. DOM ~12 months.
ON_MARKET_COMPS = [
    {"num": 1, "addr": "160 Ash Ave, Carpinteria (White Caps)", "units": 7, "yr": 1963, "sf": "--", "price": 5495000, "ppu": 785000, "psf": "--", "dom": "12 mo", "notes": "Renovated, furnished, delivered vacant, 1.5 blocks to beach. Reduced twice from $6.5M."},
]

# Rent Comps — renovated-product focus; sf=0 renders as "--" (Sea Cliff OM market rents carry no SF)
RENT_COMPS = [
    {"addr": "Sea Cliff Apartments, 20-80 Oceano Ave", "type": "2BD/1BA", "sf": 0, "rent": 4300, "rent_sf": 0, "source": "Sea Cliff OM market rent (oceanfront)"},
    {"addr": "Sea Cliff Apartments, 20-80 Oceano Ave", "type": "1BD/1BA", "sf": 0, "rent": 3750, "rent_sf": 0, "source": "Sea Cliff OM market rent (oceanfront)"},
    {"addr": "Sea Crest Apartments, 100 Oceano Ave", "type": "1BD/1BA", "sf": 780, "rent": 2950, "rent_sf": 3.78, "source": "Zumper (renovated)"},
    {"addr": "868 Highland Dr", "type": "2BD/1.5BA", "sf": 1083, "rent": 3800, "rent_sf": 3.51, "source": "Apartment List (gut-renovated)"},
    {"addr": "1021 Cliff Dr", "type": "2BD/2BA", "sf": 1090, "rent": 4995, "rent_sf": 4.58, "source": "Renovated, ocean view"},
    {"addr": "124 Oceano Ave (subject, pre-renovation)", "type": "2BD/2BA", "sf": 720, "rent": 3500, "rent_sf": 4.86, "source": "Leased 07/2025, dated condition"},
]

# Expense line items — CRITICAL: Real Estate Taxes value MUST be buyer reassessed tax (LIST_PRICE * TAX_RATE), NOT seller current Prop 13 tax — (label, current_value, note_number)
# Max 12 items. Taxes calculated dynamically from price.
expense_lines = [
    ("Real Estate Taxes", round(LIST_PRICE * TAX_RATE + FIXED_ASSESSMENTS), 1),  # buyer yr-1 reassessed
    ("Insurance", 12000, 2),
    ("Water &amp; Sewer", 5200, 3),
    ("Trash", 2450, 3),
    ("Common Area Electric", 1500, 4),
    ("Repairs &amp; Maintenance", 4200, 5),
    ("Contract Services", 1750, None),
    ("Administrative", 1000, None),
    ("Management Fee", 17442, 6),
    ("Replacement Reserves", 1400, None),
    ("Miscellaneous", 250, None),
]

# Operating Statement Notes
OS_NOTES = {
    1: "Real Estate Taxes: Buyer Year 1 tax reassessed at the list price. Santa Barbara TRA 002-001 ad valorem rate of 1.05404% plus $69.99 in flat direct assessments, verified from the current county tax bill.",
    2: "Insurance: Owner-provided coastal market estimate for the renovated building.",
    3: "Utilities: Owner pays water, sewer, and trash. In-unit gas and electric are tenant-paid on individual meters (assumed post-renovation; buyer to verify).",
    4: "Common Area Electric: Exterior and common lighting.",
    5: "Repairs &amp; Maintenance: Low end of market range, reflecting the stud-level renovation and all-new finishes.",
    6: "Management Fee: 5% of gross scheduled rent.",
    7: "Other Income: Laundry and storage income estimate.",
}

# ============================================================
# NARRATIVE CONTENT — DEAL-SPECIFIC (replace ALL)
# ============================================================

# Investment Overview
INVESTMENT_OVERVIEW_P1 = "The LAAA Team of Marcus &amp; Millichap is pleased to present 124 Oceano Ave, a fully renovated 7-unit multifamily asset on Santa Barbara's Mesa, one row from Leadbetter Beach and adjacent to Santa Barbara City College. The property consists of six 2-bedroom/2-bath units and one 1-bedroom/1-bath unit and will be delivered 100% vacant upon completion of a comprehensive stud-level renovation."
INVESTMENT_OVERVIEW_P2 = "Delivered vacant, the building lets a buyer set day-one market rents under Costa-Hawkins with no inherited tenancies, estoppels, or legacy rent schedules. Pro forma gross scheduled rent is $348,840 at rents validated by the oceanfront Sea Cliff Apartments on the same street, and a lean operating profile holds expenses near 29% of income, a conversion of gross rent to NOI that older stabilized buildings cannot match."
INVESTMENT_OVERVIEW_P3 = "Santa Barbara's permanent rent stabilization program is targeted for 2027. A renovated building delivered vacant today gives the buyer full market rents in place before the program arrives, while coastal zoning keeps competing new supply near zero. The two most relevant sales of this cycle both closed on Oceano Ave, led by the $21.15M Sea Cliff Apartments trade at an approximate 4.75% cap."

# Investment Highlights
HIGHLIGHTS = [
    ("Delivered 100% Vacant", "All seven units delivered empty at close. The buyer sets day-one market rents under Costa-Hawkins vacancy decontrol with no inherited tenancies or legacy rent schedules."),
    ("Gut-Renovated 2026", "Comprehensive stud-level renovation completing in 2026 with new flooring, paint, kitchens, baths, and finishes. Minimal near-term repairs and a clean insurance and financing story."),
    ("One Row from Leadbetter Beach", "Mesa location a half block from the sand, adjacent to Santa Barbara City College and the Great Meadow, minutes to the harbor and downtown."),
    ("Same-Street Trophy Comp", "Sea Cliff Apartments at 20-80 Oceano Ave traded in February 2025 for $21.15M at an approximate 4.75% cap and $729,310 per unit. The subject prices just inside the on-the-sand benchmark."),
    ("4.81% Pro Forma Cap at List", "Year 1 stabilized NOI of $240,464 at the $4,995,000 list price, with property taxes fully reassessed at Santa Barbara's 1.05% rate."),
    ("Lean 29% Expense Load", "Tenant-paid in-unit utilities, no elevator or pool, and all-new systems hold operating expenses near 29% of income."),
]

# Location Overview
LOCATION_P1 = "The Mesa is Santa Barbara's coastal shelf, a low-density residential neighborhood set on the bluffs between the harbor and Arroyo Burro. 124 Oceano Ave sits at the eastern edge of the Mesa, one row back from Leadbetter Beach, with the sand, the point breaks, and Shoreline Park all inside a five-minute walk."
LOCATION_P2 = "Santa Barbara City College borders the property directly to the north, with the Great Meadow and La Playa Stadium between the building and the ocean. A campus of roughly 25,000 enrolled students next to a beach generates permanent rental demand at every price point, and the harbor, the Funk Zone, and downtown State Street are all within a few minutes' drive."
LOCATION_P3 = "Supply is the other half of the story. The parcel sits inside the city's Coastal Overlay zone, where new multifamily entitlement is slow, expensive, and rare. Competing renovated product on the Mesa is effectively limited to what already exists, which is why the few buildings that trade here command the county's premium pricing."

# Location Details Table rows
LOCATION_TABLE_ROWS = [
    ("Leadbetter Beach", "1 block"),
    ("Santa Barbara City College", "Adjacent"),
    ("Shoreline Park", "0.4 miles"),
    ("Santa Barbara Harbor", "0.7 miles"),
    ("The Funk Zone", "1.5 miles"),
    ("Downtown / State Street", "2 miles"),
    ("Zoning", "R-2, Coastal Overlay (S-D-3)"),
    ("Bike Score", "68 / Bikeable"),
]

# Mission paragraphs — Central Coast resume focus (figures: live Airtable, Glen-confirmed 2026-06-11)
MISSION_P1 = "The LAAA Team has closed 465 transactions totaling $1.47B across 4,216 units, and the Central Coast is an active part of that record. Recent closings include a 32-unit Ojai portfolio at $8.25M in December 2025, an 8-unit Ventura sale in 2024, a 7-unit Goleta sale at $635,000 per unit, and an 18-unit Oxnard asset our team has now sold twice, most recently in May 2025."
MISSION_P2 = "We know this exact market. The team has sold 318 S Voluntario St in Santa Barbara twice and brought 30+ Santa Barbara and Ventura County valuation assignments through the same underwriting discipline behind this report. We are currently marketing 180 Holly Ave, a 19-unit Carpinteria asset listed at $8.95M, and a development site in Ojai."
MISSION_P3 = "What we add on Oceano Ave is buyer depth. A Santa Barbara listing marketed only to Santa Barbara buyers leaves money on the table. Our database of 30,000+ investors and a buyer pool that runs 61% 1031 exchangors puts Los Angeles and exchange capital into the bidding alongside the local families who know what the Mesa is worth."

# Buyer Profile
BUYER_TYPES = [
    ("Coastal Legacy Capital", "Santa Barbara family offices and long-term private owners who hold Mesa assets for decades. A renovated, vacant building with no tenant baggage is exactly what this buyer waits years for."),
    ("1031 Exchange Buyers", "61% of LAAA buyers are exchangors. A delivered-vacant, fully renovated coastal asset with day-one market rents is a clean upleg with no deferred-maintenance risk on a fixed timeline."),
    ("SBCC Demand Investors", "Operators who underwrite the permanent rental demand of an adjacent college campus and a beach one row away. Vacancy on the Mesa is a lease-up timeline, not a market risk."),
]
BUYER_OBJECTIONS = [
    ("Why pay a sub-5% cap?", "Sea Cliff Apartments traded at an approximate 4.75% cap on the sand a half block away in February 2025. The subject at 4.81% prices slightly cheaper than the trophy benchmark while delivering brand-new product, and matching Sea Cliff's cap would imply roughly $5.05M."),
    ("Are the pro forma rents real?", "Sea Cliff's own long-term market rents are $4,300 for 2-bedroom units and $3,750 for 1-bedrooms, oceanfront. The subject is underwritten at $4,295 and $3,200, at or below the on-the-sand evidence, and the renovated Sea Crest 1-bedroom on the same street asks $2,950. The subject's own unit leased at $3,500 in dated condition in July 2025."),
    ("What about rent control?", "The building is delivered vacant, so the buyer sets initial rents at full market under Costa-Hawkins. AB 1482 then caps annual increases. The city's permanent rent program, targeted for 2027, regulates future increases, not the going-in rents a vacant building lets you set today."),
]
BUYER_CLOSING = "From legacy coastal capital to exchange buyers on a clock, 124 Oceano Ave offers what almost never reaches this market: a renovated, vacant, beach-block building with day-one market economics."

# Comp Narratives — same-street set (Glen-locked): the entire comp story lives on Oceano Ave
COMP_NARRATIVES = """<p class="narrative"><strong>1. Sea Cliff Apartments, 20-80 Oceano Ave (Oceanfront).</strong> The 29-unit Sea Cliff Apartments traded in February 2025 for $21,150,000, or $729,310 per unit, after being offered at $25M. On the income in its offering, which included nine short-term vacation rentals, the closing price reflects an approximate 4.75% cap and a 12 GRM. Sea Cliff sits on the sand overlooking Leadbetter Beach, a half block from the subject, and it is the benchmark this pricing is built against: matching its 4.75% cap implies roughly $5,050,000 for the subject, so the list price asks slightly more cap for a location one row back. Its offering also carried long-term market rents of $4,300 for 2-bedroom units and $3,750 for 1-bedrooms, direct support for the subject's pro forma.</p>
<p class="narrative"><strong>2. 330 Oceano Ave.</strong> Three blocks up the same street, this 5-unit 1965 building sold in November 2024 for $2,950,000, or $590,000 per unit, after a hold of more than 20 years and with original-condition interiors. It is the unrenovated floor for the street: an older, smaller building with no renovation story still commanded $590,000 per unit, which frames the premium a fully renovated, delivered-vacant building earns above it.</p>"""

# On-Market Narrative — 160 Ash Ave active competition (Glen-directed 2026-06-11)
ON_MARKET_NARRATIVE = """<strong>160 Ash Ave, Carpinteria (White Caps).</strong> The only directly competitive offering on the market is this fully renovated 7-unit building a block and a half from Carpinteria State Beach: seven 2-bedroom/1-bath units, sold furnished and delivered vacant, with 9 parking spaces and on-site laundry. It came to market in June 2025 at $6,500,000 and has taken two reductions, to $5,900,000 in July and to its current $5,495,000 in September 2025, $785,000 per unit after roughly 12 months of exposure. The subject lists at $713,571 per unit, below the standing competition, with larger 2-bedroom/2-bath floor plans in the stronger Santa Barbara Mesa location next to SBCC and Leadbetter Beach. A buyer comparing the two renovated, delivered-vacant coastal offerings finds the subject priced $71,429 per unit under the alternative that has not traded."""

# Pricing Rationale
PRICING_RATIONALE = "The $4,995,000 list price is anchored to the only two relevant trades of this cycle, both on the subject's own street. Sea Cliff Apartments closed in February 2025 at an approximate 4.75% cap and $729,310 per unit on the sand; pricing the subject at Sea Cliff's exact cap would imply roughly $5,050,000, so the list asks a slightly higher cap for a location one row back. The unrenovated 330 Oceano print at $590,000 per unit defines the floor a renovated, vacant building clears. At list, the subject shows a 4.81% pro forma cap on Year 1 NOI of $240,464 with property taxes fully reassessed, $713,571 per unit, and a 14.3 GRM whose spread to Sea Cliff's 12 reflects a 29% expense ratio against the trophy's roughly 40%. Sales from November 2024 through February 2025 frame the range, and we expect a trade between $4,750,000 and $4,995,000. The active market confirms the positioning: the only competing renovated 7-unit coastal offering, 160 Ash Ave in Carpinteria, asks $785,000 per unit and has sat about 12 months through two reductions from $6.5M, while the subject lists at $713,571 per unit."

# Confidence levels are never displayed client-facing
COMP_CONFIDENCE = "MODERATE"

# Assumptions & Conditions disclaimer
ASSUMPTIONS_DISCLAIMER = "This analysis is based on information provided by ownership and third-party sources deemed reliable. Typical unit square footage reflects a Hover interior scan of one representative 2-bedroom unit (August 2025, 638 SF of interior rooms, approximately 720 SF gross including walls); remaining unit and building square footages blend that measurement with owner plans and are subject to verification. Year built is estimated; the county assessor does not publish a construction year for this parcel, and the estimate reflects the vintage of comparable Oceano Ave multifamily. Operating figures are presented pro forma at delivery of a fully renovated, vacant building; individual utility metering is assumed pending confirmation. Buyer should independently verify all information during due diligence. Pro forma projections are estimates and not guaranteed."

# Property Info Tables (4 tables for Property Details page) — SB-correct, no LA boilerplate
PROP_OVERVIEW = [
    ("Address", FULL_ADDRESS),
    ("APN", "045-230-003"),
    ("Units", "7 (six 2BD/2BA, one 1BD/1BA)"),
    ("Building SF", "&plusmn;5,175 SF (Hover-measured typical unit + owner plans; buyer to verify)"),
    ("Lot Size", "9,147 SF (0.21 acres)"),
    ("Stories", "2"),
    ("Year Built", "Circa 1965, estimated (not on county record; consistent with comparable Oceano Ave multifamily built 1961-1965)"),
    ("Condition", "Fully renovated 2026 (stud-level)"),
    ("Occupancy at Delivery", "100% vacant"),
]
PROP_SITE_ZONING = [
    ("Zoning", "R-2 (City of Santa Barbara)"),
    ("Overlay", "S-D-3 Coastal Overlay (SBMC 28.44)"),
    ("Coastal Jurisdiction", "City permit area, non-appealable zone"),
    ("Subdivision", "Granthurst, Lot 2"),
    ("Opportunity Zone", "No"),
    ("Hazard Flags", "None present per parcel report"),
]
PROP_BUILDING = [
    ("Construction", "Wood frame with stucco exterior"),
    ("Renovation", "Stud-level renovation completing 2026; all-new interiors and finishes"),
    ("Parking", "Off-street, including covered tuck-under (buyer to verify count)"),
    ("Laundry", "On-site (final configuration to be confirmed)"),
    ("Metering", "Individual gas and electric assumed; buyer to verify"),
]
PROP_REGULATORY = [
    ("State Rent Caps", "CA AB 1482 applies"),
    ("Local Ordinance", "City of Santa Barbara just cause (SBMC 26.50)"),
    ("Local Rent Program", "Permanent rent stabilization in process, targeted 2027"),
    ("Initial Rents", "Delivered vacant; buyer sets market rents at lease-up (Costa-Hawkins)"),
    ("Opportunity Zone", "No"),
]

# Transaction History (optional)
TRANSACTION_ROWS = []  # DEAL-SPECIFIC — list of dicts
TRANSACTION_NARRATIVE = ""  # DEAL-SPECIFIC

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def fc(n):
    """Format currency."""
    if n is None or n == "--":
        return "--"
    return f"${n:,.0f}"

def fp(n):
    """Format percentage."""
    if n is None:
        return "--"
    return f"{n:.2f}%"

# ============================================================
# LEAFLET JS MAP GENERATOR
# ============================================================
def build_map_js(map_id, comps, comp_color, addr_dict, subject_lat, subject_lng, subject_label=None):
    """Google Maps JS (hard rule: Google Maps only). Emits init code consumed inside initMaps()."""
    if subject_label is None:
        subject_label = ADDRESS
    js = f"""var {map_id}El = document.getElementById('{map_id}');
if ({map_id}El) {{
  var {map_id} = new google.maps.Map({map_id}El, {{mapTypeId: 'roadmap', mapTypeControl: false, streetViewControl: false, fullscreenControl: true}});
  var {map_id}B = new google.maps.LatLngBounds();
  var {map_id}Info = new google.maps.InfoWindow();
  function {map_id}Add(lat, lng, label, color, scale, html) {{
    var mk = new google.maps.Marker({{
      position: {{lat: lat, lng: lng}}, map: {map_id},
      icon: {{path: google.maps.SymbolPath.CIRCLE, scale: scale, fillColor: color, fillOpacity: 1, strokeColor: '#ffffff', strokeWeight: 2}},
      label: {{text: label, color: '#ffffff', fontWeight: '700', fontSize: '12px'}}
    }});
    mk.addListener('click', function() {{ {map_id}Info.setContent(html); {map_id}Info.open({map_id}, mk); }});
    {map_id}B.extend({{lat: lat, lng: lng}});
  }}
  {map_id}Add({subject_lat}, {subject_lng}, '\\u2605', '#C5A258', 16, '<b>{subject_label}</b><br>Subject Property<br>{UNITS} Units');
"""
    tier3_color = "#9E9E9E"
    for i, c in enumerate(comps):
        lat, lng = None, None
        for a, coords in addr_dict.items():
            if coords and c["addr"].lower() in a.lower():
                lat, lng = coords
                break
        if lat is None:
            continue
        label = str(i + 1)
        marker_color = tier3_color if c.get("tier", 1) == 3 else comp_color
        price_str = fc(c.get("price", 0))
        popup = f"<b>#{label}: {c['addr']}</b><br>{c.get('units', '')} Units" + (f" | {price_str}" if c.get("price") else "")
        js += f"  {map_id}Add({lat}, {lng}, '{label}', '{marker_color}', 13, '{popup}');\n"
    js += f"  {map_id}.fitBounds({map_id}B, 48);\n}}\n"
    return js

# Generate Leaflet JS for each comp section
sale_map_js = build_map_js("saleMap", SALE_COMPS, "#1B3A5C", COMP_ADDRESSES, SUBJECT_LAT, SUBJECT_LNG)
# On-market map intentionally disabled: 160 Ash Ave (Carpinteria) sits ~9 miles down-coast,
# far outside the same-street comp frame, and no resolved rooftop pin exists for it.
active_map_js = ""
rent_comps_for_map = [{"addr": rc["addr"], "units": "", "price": 0} for rc in RENT_COMPS]
rent_map_js = build_map_js("rentMap", rent_comps_for_map, "#1B3A5C", RENT_COMP_ADDRESSES, SUBJECT_LAT, SUBJECT_LNG)

# ============================================================
# GENERATE STATIC MAPS
# ============================================================
print("\nGenerating static maps...")
IMG["loc_map"] = generate_static_map(SUBJECT_LAT, SUBJECT_LNG,
    [{"lat": SUBJECT_LAT, "lng": SUBJECT_LNG, "label": "★", "color": "#C5A258"}],
    width=800, height=220, zoom=15)

sale_markers = build_markers_from_comps(SALE_COMPS, COMP_ADDRESSES, "#1B3A5C", SUBJECT_LAT, SUBJECT_LNG)
IMG["sale_map_static"] = generate_static_map(SUBJECT_LAT, SUBJECT_LNG, sale_markers,
    width=800, height=300, zoom=calc_auto_zoom(sale_markers))

# On-market static map skipped (see active_map_js note above)

rent_markers = build_markers_from_comps(rent_comps_for_map, RENT_COMP_ADDRESSES, "#1B3A5C", SUBJECT_LAT, SUBJECT_LNG)
IMG["rent_map_static"] = generate_static_map(SUBJECT_LAT, SUBJECT_LNG, rent_markers,
    width=800, height=300, zoom=calc_auto_zoom(rent_markers))

# ============================================================
# GENERATE DYNAMIC TABLE HTML
# ============================================================

# Rent Roll
rent_roll_html = ""
total_rent = 0
total_sf = 0
total_market = 0
if PROPERTY_TYPE == "value-add":
    for unit, utype, sf, cur_rent, mkt_rent in RENT_ROLL:
        total_rent += cur_rent
        total_sf += sf
        total_market += mkt_rent
        rent_roll_html += f'<tr><td>{unit}</td><td>{utype}</td><td class="num">{sf:,}</td><td class="num">${cur_rent:,}</td><td class="num">${cur_rent/sf:.2f}</td><td class="num">${mkt_rent:,}</td><td class="num">${mkt_rent/sf:.2f}</td></tr>\n'
    rent_roll_html += f'<tr style="background:#1B3A5C;color:#fff;font-weight:700;"><td>Total</td><td>{len(RENT_ROLL)} Units</td><td class="num">{total_sf:,}</td><td class="num">${total_rent:,}</td><td class="num">${total_rent/total_sf:.2f}</td><td class="num">${total_market:,}</td><td class="num">${total_market/total_sf:.2f}</td></tr>\n'
else:
    for unit, utype, sf, rent, status, notes in RENT_ROLL:
        total_rent += rent
        total_sf += sf
        status_cell = f'<strong>{status}</strong>' if status == "Vacant" else status
        rent_roll_html += f'<tr><td>{unit}</td><td>{utype}</td><td class="num">{sf:,}</td><td class="num">${rent:,}</td><td class="num">${rent/sf:.2f}</td><td>{status_cell}</td><td>{notes}</td></tr>\n'
    rent_roll_html += f'<tr style="background:#1B3A5C;color:#fff;font-weight:700;"><td>Total</td><td>{len(RENT_ROLL)} Units</td><td class="num">{total_sf:,}</td><td class="num">${total_rent:,}</td><td class="num">${total_rent/total_sf:.2f}</td><td></td><td>${total_rent*12:,}/yr</td></tr>\n'

# Sale Comp Table — sorted by tier (Tier 1 first, LAAA sales first within tier)
sale_comp_html = ""
sorted_comps = sorted(SALE_COMPS, key=lambda c: (c.get("tier", 1), 0 if c.get("laaa") else 1))
for c in sorted_comps:
    grm_str = f'{c["grm"]:.1f}x' if c.get("grm") not in (None, "--") else "--"
    cap_str = f'{c["cap"]:.2f}%' if c.get("cap") not in (None, "--") else "--"
    psf_str = f'${c["psf"]:,}' if c.get("psf") not in (None, "--") else "--"
    dom_str = f'{c["dom"]:,}' if c.get("dom") not in (None, "--") else "--"
    sf_str = f'{c["sf"]:,}' if c.get("sf") not in (None, "--") else "--"
    # LAAA Team badge + tier indicator in address cell
    addr_display = c["addr"]
    if c.get("laaa"):
        addr_display += ' <span style="background:#C5A258;color:#fff;font-size:8px;font-weight:700;padding:1px 4px;border-radius:2px;vertical-align:middle;">LAAA TEAM</span>'
    sale_comp_html += f'<tr><td>{c["num"]}</td><td>{addr_display}</td><td class="num">{c["units"]}</td>'
    sale_comp_html += f'<td>{c["yr"]}</td><td class="num">{sf_str}</td>'
    sale_comp_html += f'<td class="num">{fc(c["price"])}</td><td class="num">{fc(c["ppu"])}</td>'
    sale_comp_html += f'<td class="num">{psf_str}</td><td class="num">{cap_str}</td>'
    sale_comp_html += f'<td class="num">{grm_str}</td>'
    sale_comp_html += f'<td>{c["date"]}</td><td class="num">{dom_str}</td></tr>\n'

# Average, median, and Tier 1 average summary rows
if SALE_COMPS:
    sc_prices = [c["price"] for c in SALE_COMPS]
    sc_ppus = [c["ppu"] for c in SALE_COMPS]
    sc_psfs = [c["psf"] for c in SALE_COMPS if c.get("psf") not in (None, "--")]
    sc_caps = [c["cap"] for c in SALE_COMPS if c.get("cap") not in (None, "--")]
    sc_grms = [c["grm"] for c in SALE_COMPS if c.get("grm") not in (None, "--")]
    sc_doms = [c["dom"] for c in SALE_COMPS if c.get("dom") not in (None, "--")]

    avg_price = statistics.mean(sc_prices)
    avg_ppu = statistics.mean(sc_ppus)
    avg_psf = statistics.mean(sc_psfs) if sc_psfs else 0
    avg_cap_str = f'{statistics.mean(sc_caps):.2f}%' if sc_caps else "--"
    avg_grm_str = f'{statistics.mean(sc_grms):.1f}x' if sc_grms else "--"
    avg_dom_str = f'{statistics.mean(sc_doms):.0f}' if sc_doms else "--"
    med_price = statistics.median(sc_prices)
    med_ppu = statistics.median(sc_ppus)
    med_psf = statistics.median(sc_psfs) if sc_psfs else 0
    med_cap_str = f'{statistics.median(sc_caps):.2f}%' if sc_caps else "--"
    med_grm_str = f'{statistics.median(sc_grms):.1f}x' if sc_grms else "--"
    med_dom_str = f'{statistics.median(sc_doms):.0f}' if sc_doms else "--"

    # Tier 1 average (if any Tier 1 comps exist)
    t1_comps = [c for c in SALE_COMPS if c.get("tier") == 1]
    t1_row = ""
    if t1_comps:
        t1_ppus = [c["ppu"] for c in t1_comps]
        t1_psfs = [c["psf"] for c in t1_comps if c.get("psf") not in (None, "--")]
        t1_caps = [c["cap"] for c in t1_comps if c.get("cap") not in (None, "--")]
        t1_grms = [c["grm"] for c in t1_comps if c.get("grm") not in (None, "--")]
        t1_ppu = statistics.mean(t1_ppus)
        t1_psf_str = f'${statistics.mean(t1_psfs):,.0f}' if t1_psfs else "--"
        t1_cap_str = f'{statistics.mean(t1_caps):.2f}%' if t1_caps else "--"
        t1_grm_str = f'{statistics.mean(t1_grms):.1f}x' if t1_grms else "--"
        t1_style = 'style="background:#E8F0E8;font-weight:600;"'
        t1_row = f'<tr {t1_style}><td></td><td>Tier 1 Average</td><td class="num"></td><td></td><td class="num"></td>'
        t1_row += f'<td class="num"></td><td class="num">{fc(t1_ppu)}</td>'
        t1_row += f'<td class="num">{t1_psf_str}</td><td class="num">{t1_cap_str}</td>'
        t1_row += f'<td class="num">{t1_grm_str}</td>'
        t1_row += f'<td></td><td class="num"></td></tr>\n'

    summary_row_style = 'style="background:#FFF8E7;font-weight:600;"'
    sale_comp_html += f'<tr {summary_row_style}><td></td><td>Average</td><td class="num"></td><td></td><td class="num"></td>'
    sale_comp_html += f'<td class="num">{fc(avg_price)}</td><td class="num">{fc(avg_ppu)}</td>'
    sale_comp_html += f'<td class="num">${avg_psf:,.0f}</td><td class="num">{avg_cap_str}</td>'
    sale_comp_html += f'<td class="num">{avg_grm_str}</td>'
    sale_comp_html += f'<td></td><td class="num">{avg_dom_str}</td></tr>\n'
    sale_comp_html += f'<tr {summary_row_style}><td></td><td>Median</td><td class="num"></td><td></td><td class="num"></td>'
    sale_comp_html += f'<td class="num">{fc(med_price)}</td><td class="num">{fc(med_ppu)}</td>'
    sale_comp_html += f'<td class="num">${med_psf:,.0f}</td><td class="num">{med_cap_str}</td>'
    sale_comp_html += f'<td class="num">{med_grm_str}</td>'
    sale_comp_html += f'<td></td><td class="num">{med_dom_str}</td></tr>\n'
    if t1_row:
        sale_comp_html += t1_row

# On-Market Comp Table
on_market_html = ""
for c in ON_MARKET_COMPS:
    psf_str = f'${c["psf"]}' if c.get("psf") and c["psf"] != "--" else "--"
    sf_str = f'{c["sf"]:,}' if c.get("sf") and c["sf"] != "--" else "--"
    on_market_html += f'<tr><td>{c["num"]}</td><td>{c["addr"]}</td><td class="num">{c["units"]}</td>'
    on_market_html += f'<td>{c["yr"]}</td><td class="num">{sf_str}</td>'
    on_market_html += f'<td class="num">{fc(c["price"])}</td><td class="num">{fc(c["ppu"])}</td>'
    on_market_html += f'<td class="num">{psf_str}</td><td class="num">{c["dom"]}</td>'
    on_market_html += f'<td>{c["notes"]}</td></tr>\n'

# Rent Comp Table (sf=0 renders as "--" for OM-sourced market rents without SF)
rent_comp_html = ""
for i, rc in enumerate(RENT_COMPS, 1):
    sf_str = f'{rc["sf"]:,}' if rc.get("sf") else "--"
    rsf_str = f'${rc["rent_sf"]:.2f}' if rc.get("rent_sf") else "--"
    rent_comp_html += f'<tr><td>{i}</td><td>{rc["addr"]}</td><td>{rc["type"]}</td>'
    rent_comp_html += f'<td class="num">{sf_str}</td><td class="num">${rc["rent"]:,}</td>'
    rent_comp_html += f'<td class="num">{rsf_str}</td><td>{rc["source"]}</td></tr>\n'

# Operating Statement
TAXES_AT_LIST = AT_LIST["taxes"]
CUR_EGI = AT_LIST["cur_egi"]

os_income_html = ""
vacancy_amt = GSR * VACANCY_PCT
eri = GSR - vacancy_amt
os_income_html += f'<tr><td>Gross Scheduled Rent</td><td class="num">${GSR:,.0f}</td><td class="num">${GSR/UNITS:,.0f}</td><td class="num">${GSR/SF:.2f}</td><td class="num"> - </td></tr>\n'
os_income_html += f'<tr><td>Less: Vacancy ({VACANCY_PCT*100:.0f}%)</td><td class="num">$({vacancy_amt:,.0f})</td><td class="num">$({vacancy_amt/UNITS:,.0f})</td><td class="num">$({vacancy_amt/SF:.2f})</td><td class="num"> - </td></tr>\n'
if OTHER_INCOME > 0:
    os_income_html += f'<tr><td>Other Income <span class="note-ref">[7]</span></td><td class="num">${OTHER_INCOME:,.0f}</td><td class="num">${OTHER_INCOME/UNITS:,.0f}</td><td class="num">${OTHER_INCOME/SF:.2f}</td><td class="num"> - </td></tr>\n'
os_income_html += f'<tr class="summary"><td><strong>Effective Gross Income</strong></td><td class="num"><strong>${CUR_EGI:,.0f}</strong></td><td class="num"><strong>${CUR_EGI/UNITS:,.0f}</strong></td><td class="num"><strong>${CUR_EGI/SF:.2f}</strong></td><td class="num"><strong>100.0%</strong></td></tr>\n'

os_expense_html = ""
total_exp_calc = 0
for label, val, note_num in expense_lines:
    total_exp_calc += val
    ref = f' <span class="note-ref">[{note_num}]</span>' if note_num else ""
    os_expense_html += f'<tr><td>{label}{ref}</td><td class="num">${val:,.0f}</td><td class="num">${val/UNITS:,.0f}</td><td class="num">${val/SF:.2f}</td><td class="num">{val/CUR_EGI*100:.1f}%</td></tr>\n'

NOI_AT_LIST = CUR_EGI - total_exp_calc
os_expense_html += f'<tr class="summary"><td><strong>Total Expenses</strong></td><td class="num"><strong>${total_exp_calc:,.0f}</strong></td><td class="num"><strong>${total_exp_calc/UNITS:,.0f}</strong></td><td class="num"><strong>${total_exp_calc/SF:.2f}</strong></td><td class="num"><strong>{total_exp_calc/CUR_EGI*100:.1f}%</strong></td></tr>\n'
os_expense_html += f'<tr class="summary"><td><strong>Net Operating Income</strong></td><td class="num"><strong>${NOI_AT_LIST:,.0f}</strong></td><td class="num"><strong>${NOI_AT_LIST/UNITS:,.0f}</strong></td><td class="num"><strong>${NOI_AT_LIST/SF:.2f}</strong></td><td class="num"><strong>{NOI_AT_LIST/CUR_EGI*100:.1f}%</strong></td></tr>\n'

# OS Notes HTML
os_notes_html = ""
for num in sorted(OS_NOTES.keys()):
    os_notes_html += f'<p><strong>[{num}]</strong> {OS_NOTES[num]}</p>\n'

# Pricing Matrix
matrix_html = ""
if PROPERTY_TYPE == "value-add":
    for m in MATRIX:
        cls = ' class="highlight"' if m["price"] == LIST_PRICE else ""
        matrix_html += f'<tr{cls}><td class="num">${m["price"]:,}</td>'
        matrix_html += f'<td class="num">{m["cur_cap"]:.2f}%</td>'
        matrix_html += f'<td class="num">{m["pf_cap"]:.2f}%</td>'
        matrix_html += f'<td class="num">{m["coc_cur"]:.2f}%</td>'
        matrix_html += f'<td class="num">${m["per_sf"]:.0f}</td>'
        matrix_html += f'<td class="num">${m["per_unit"]:,.0f}</td>'
        matrix_html += f'<td class="num">{m["pf_grm"]:.2f}x</td></tr>\n'
else:
    for m in MATRIX:
        cls = ' class="highlight"' if m["price"] == LIST_PRICE else ""
        matrix_html += f'<tr{cls}><td class="num">${m["price"]:,}</td>'
        matrix_html += f'<td class="num">{m["cur_cap"]:.2f}%</td>'
        matrix_html += f'<td class="num">{m["coc_cur"]:.2f}%</td>'
        matrix_html += f'<td class="num">${m["per_unit"]:,.0f}</td>'
        matrix_html += f'<td class="num">${m["per_sf"]:.0f}</td>'
        matrix_html += f'<td class="num">{m["grm"]:.2f}x</td>'
        matrix_html += f'<td class="num">{m["dcr_cur"]:.2f}x</td></tr>\n'

# Summary page expense rows
sum_expense_html = ""
for label, val, _ in expense_lines:
    label_clean = label.replace("&amp;", "&")
    sum_expense_html += f'<tr><td>{label_clean}</td><td class="num">${val:,.0f}</td></tr>\n'

if LIST_PRICE > 0:
    print(f"NOI at list (reassessed): ${NOI_AT_LIST:,.0f}")
    print(f"Total expenses: ${total_exp_calc:,.0f}")

# ============================================================
# HTML ASSEMBLY
# ============================================================
html_parts = []

# HEAD
html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta property="og:title" content="Broker Opinion of Value - {FULL_ADDRESS}">
<meta property="og:description" content="{PROPERTY_SUBTITLE} - {CITY_STATE_ZIP} | LAAA Team - Marcus &amp; Millichap">
<meta property="og:image" content="{BOV_BASE_URL}/preview.png">
<meta property="og:url" content="{BOV_BASE_URL}/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Broker Opinion of Value - {FULL_ADDRESS}">
<meta name="twitter:description" content="{PROPERTY_SUBTITLE} - {CITY_STATE_ZIP} | LAAA Team - Marcus &amp; Millichap">
<meta name="twitter:image" content="{BOV_BASE_URL}/preview.png">
<title>BOV - {FULL_ADDRESS} | LAAA Team</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<!-- Maps: Google Maps JS API, loaded at end of body (hard rule: Google Maps only) -->
<style>
""")

# ============================================================
# DESKTOP CSS (verbatim from blueprint)
# ============================================================
html_parts.append("""
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; color: #333; line-height: 1.6; background: #fff; }
html { scroll-padding-top: 50px; }
p { margin-bottom: 16px; font-size: 14px; line-height: 1.7; }

/* Cover */
.cover { position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; text-align: center; color: #fff; overflow: hidden; }
.cover-bg { position: absolute; inset: 0; background-size: cover; background-position: center; filter: brightness(0.45); z-index: 0; }
.cover-content { position: relative; z-index: 2; padding: 60px 40px; max-width: 860px; }
.cover-logo { width: 320px; margin: 0 auto 30px; display: block; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3)); }
.cover-label { font-size: 13px; font-weight: 500; letter-spacing: 3px; text-transform: uppercase; color: #C5A258; margin-bottom: 18px; }
.cover-title { font-size: 46px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; text-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.cover-stats { display: flex; gap: 32px; justify-content: center; flex-wrap: wrap; margin-bottom: 32px; }
.cover-stat-value { display: block; font-size: 26px; font-weight: 600; color: #fff; }
.cover-stat-label { display: block; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; color: #C5A258; margin-top: 4px; }
.cover-headshots { display: flex; justify-content: center; gap: 40px; margin-top: 24px; margin-bottom: 16px; }
.cover-headshot { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #C5A258; object-fit: cover; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.cover-headshot-name { font-size: 12px; font-weight: 600; margin-top: 6px; color: #fff; }
.cover-headshot-title { font-size: 10px; color: #C5A258; }
.cover-headshot-wrap { text-align: center; }
.cover-stat { text-align: center; }
.cover-address { font-size: 16px; font-weight: 400; letter-spacing: 1px; color: rgba(255,255,255,0.85); margin-top: 4px; }
.client-greeting { font-size: 14px; font-weight: 500; color: #C5A258; letter-spacing: 1px; margin-top: 16px; }
.gold-line { height: 3px; background: #C5A258; margin: 20px 0; }

/* PDF Download Button */
.pdf-float-btn { position: fixed; bottom: 24px; right: 24px; z-index: 9999; padding: 14px 28px; background: #C5A258; color: #1B3A5C; font-size: 14px; font-weight: 700; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.35); display: flex; align-items: center; gap: 8px; }
.pdf-float-btn:hover { background: #fff; transform: translateY(-2px); }
.pdf-float-btn svg { width: 18px; height: 18px; fill: currentColor; }

/* TOC Nav */
.toc-nav { background: #1B3A5C; padding: 0 12px; display: flex; flex-wrap: nowrap; justify-content: center; align-items: stretch; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.15); overflow-x: auto; scrollbar-width: none; }
.toc-nav::-webkit-scrollbar { display: none; }
.toc-nav a { color: rgba(255,255,255,0.85); text-decoration: none; font-size: 11px; font-weight: 500; letter-spacing: 0.3px; text-transform: uppercase; padding: 12px 8px; border-bottom: 2px solid transparent; white-space: nowrap; display: flex; align-items: center; }
.toc-nav a:hover { color: #fff; background: rgba(197,162,88,0.12); border-bottom-color: rgba(197,162,88,0.4); }
.toc-nav a.toc-active { color: #C5A258; font-weight: 600; border-bottom-color: #C5A258; }

/* Sections */
.section { padding: 50px 40px; max-width: 1100px; margin: 0 auto; }
.section-alt { background: #f8f9fa; }
.section-title { font-size: 26px; font-weight: 700; color: #1B3A5C; margin-bottom: 6px; }
.section-subtitle { font-size: 13px; color: #C5A258; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 16px; font-weight: 500; }
.section-divider { width: 60px; height: 3px; background: #C5A258; margin-bottom: 30px; }
.sub-heading { font-size: 18px; font-weight: 600; color: #1B3A5C; margin: 30px 0 16px; }

/* Metrics */
.metrics-grid, .metrics-grid-4 { display: grid; gap: 16px; margin-bottom: 30px; }
.metrics-grid { grid-template-columns: repeat(3, 1fr); }
.metrics-grid-4 { grid-template-columns: repeat(4, 1fr); }
.metric-card { background: #1B3A5C; border-radius: 12px; padding: 24px; text-align: center; color: #fff; }
.metric-value { display: block; font-size: 28px; font-weight: 700; }
.metric-label { display: block; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.6); margin-top: 6px; }
.metric-sub { display: block; font-size: 12px; color: #C5A258; margin-top: 4px; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }
th { background: #1B3A5C; color: #fff; padding: 10px 12px; text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
td { padding: 8px 12px; border-bottom: 1px solid #eee; }
tr:nth-child(even) { background: #f5f5f5; }
tr.highlight { background: #FFF8E7 !important; border-left: 3px solid #C5A258; }
td.num, th.num { text-align: right; }
.table-scroll { overflow-x: auto; margin-bottom: 24px; }
.table-scroll table { min-width: 700px; margin-bottom: 0; }
.info-table td { padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 13px; }
.info-table td:first-child { font-weight: 600; color: #1B3A5C; width: 40%; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }

/* Track Record */
.tr-tagline { font-size: 24px; font-weight: 600; color: #1B3A5C; text-align: center; padding: 16px 24px; margin-bottom: 20px; border-left: 4px solid #C5A258; background: #FFF8E7; border-radius: 0 4px 4px 0; font-style: italic; }
.tr-map-print { display: none; }
.tr-service-quote { margin: 24px 0; }
.tr-service-quote h3 { font-size: 18px; font-weight: 700; color: #1B3A5C; margin-bottom: 8px; }
.tr-service-quote p { font-size: 14px; line-height: 1.7; }
.bio-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }
.bio-card { display: flex; gap: 16px; align-items: flex-start; }
.bio-headshot { width: 100px; height: 100px; border-radius: 50%; border: 3px solid #C5A258; object-fit: cover; flex-shrink: 0; }
.bio-name { font-size: 16px; font-weight: 700; color: #1B3A5C; }
.bio-title { font-size: 11px; color: #C5A258; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.bio-text { font-size: 13px; line-height: 1.6; color: #444; }
.team-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 12px 0; }
.team-card { text-align: center; padding: 8px; }
.team-headshot { width: 60px; height: 60px; border-radius: 50%; border: 2px solid #C5A258; object-fit: cover; margin: 0 auto 4px; display: block; }
.team-card-name { font-size: 13px; font-weight: 700; color: #1B3A5C; }
.team-card-title { font-size: 10px; color: #C5A258; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.costar-badge { text-align: center; background: #FFF8E7; border: 2px solid #C5A258; border-radius: 8px; padding: 20px 24px; margin: 30px auto 24px; max-width: 600px; }
.costar-badge-title { font-size: 22px; font-weight: 700; color: #1B3A5C; }
.costar-badge-sub { font-size: 12px; color: #C5A258; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-top: 6px; }
.condition-note { background: #FFF8E7; border-left: 4px solid #C5A258; padding: 16px 20px; margin: 24px 0; border-radius: 0 4px 4px 0; font-size: 13px; line-height: 1.6; }
.condition-note-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #C5A258; margin-bottom: 8px; }
.achievements-list { font-size: 13px; line-height: 1.8; }
.note-ref { font-size: 9px; color: #C5A258; font-weight: 700; vertical-align: super; }

/* Marketing */
.mkt-quote { background: #FFF8E7; border-left: 4px solid #C5A258; padding: 16px 24px; margin: 20px 0; border-radius: 0 4px 4px 0; font-size: 15px; font-style: italic; line-height: 1.6; color: #1B3A5C; }
.mkt-channels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
.mkt-channel { background: #f0f4f8; border-radius: 8px; padding: 16px 20px; }
.mkt-channel h4 { color: #1B3A5C; font-size: 14px; margin-bottom: 8px; }
.mkt-channel li { font-size: 13px; line-height: 1.5; margin-bottom: 4px; }
.perf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
.perf-card { background: #f0f4f8; border-radius: 8px; padding: 16px 20px; }
.perf-card h4 { color: #1B3A5C; font-size: 14px; margin-bottom: 8px; }
.perf-card li { font-size: 13px; line-height: 1.5; margin-bottom: 4px; }
.platform-strip { display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap; margin-top: 24px; padding: 14px 20px; background: #1B3A5C; border-radius: 6px; }
.platform-strip-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: #C5A258; font-weight: 600; }
.platform-name { font-size: 12px; font-weight: 600; color: #fff; }

/* Press Strip */
.press-strip { display: flex; justify-content: center; align-items: center; gap: 28px; flex-wrap: wrap; margin: 16px 0 0; padding: 12px 20px; background: #f0f4f8; border-radius: 6px; }
.press-strip-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: #888; font-weight: 600; }
.press-logo { font-size: 13px; font-weight: 700; color: #1B3A5C; letter-spacing: 0.5px; }

/* Investment Overview */
.inv-split { display: grid; grid-template-columns: 50% 50%; gap: 24px; }
.inv-left .metrics-grid-4 { grid-template-columns: repeat(2, 1fr); }
.inv-text p { font-size: 13px; line-height: 1.6; margin-bottom: 10px; }
.inv-logo { display: none; }
.inv-right { display: flex; flex-direction: column; gap: 16px; padding-top: 70px; }
.inv-photo { height: 280px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.inv-photo img { width: 100%; height: 100%; object-fit: cover; object-position: center; }
.inv-highlights { background: #f0f4f8; border: 1px solid #dce3eb; border-radius: 8px; padding: 16px 20px; flex: 1; }
.inv-highlights h4 { color: #1B3A5C; font-size: 13px; margin-bottom: 8px; }
.inv-highlights li { font-size: 12px; line-height: 1.5; margin-bottom: 5px; }

/* Location */
.loc-grid { display: grid; grid-template-columns: 58% 42%; gap: 28px; align-items: start; }
.loc-left { max-height: 480px; overflow: hidden; }
.loc-left p { font-size: 13.5px; line-height: 1.7; margin-bottom: 14px; }
.loc-right { display: block; max-height: 480px; overflow: hidden; }
.loc-wide-map { width: 100%; height: 200px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-top: 20px; }
.loc-wide-map img { width: 100%; height: 100%; object-fit: cover; object-position: center; }

/* Property Details */
.prop-grid-4 { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: auto auto; gap: 20px; }

/* Operating Statement */
.os-two-col { display: grid; grid-template-columns: 55% 45%; gap: 24px; align-items: stretch; margin-bottom: 24px; }
.os-left { }
.os-right { font-size: 10.5px; line-height: 1.45; color: #555; background: #f8f9fb; border: 1px solid #e0e4ea; border-radius: 6px; padding: 16px 20px; }
.os-right h3 { font-size: 13px; margin: 0 0 8px; }
.os-right p { margin-bottom: 4px; }

/* Financial Summary */
.summary-page { margin-top: 24px; border: 1px solid #dce3eb; border-radius: 8px; padding: 20px; background: #fff; }
.summary-banner { text-align: center; background: #1B3A5C; color: #fff; padding: 10px 16px; font-size: 14px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; border-radius: 4px; margin-bottom: 16px; }
.summary-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
.summary-left { }
.summary-right { }
.summary-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 12px; border: 1px solid #dce3eb; }
.summary-table th, .summary-table td { padding: 4px 8px; border-bottom: 1px solid #e8ecf0; }
.summary-header { background: #1B3A5C; color: #fff; padding: 5px 8px !important; font-size: 10px !important; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }
.summary-table tr.summary td { border-top: 2px solid #1B3A5C; font-weight: 700; background: #f0f4f8; }
.summary-table tr:nth-child(even) { background: #fafbfc; }
.summary-trade-range { text-align: center; margin: 24px auto; padding: 16px 24px; border: 2px solid #1B3A5C; border-radius: 6px; max-width: 480px; }
.summary-trade-label { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #555; font-weight: 600; margin-bottom: 6px; }
.summary-trade-prices { font-size: 26px; font-weight: 700; color: #1B3A5C; }

/* Price Reveal */
.price-reveal { margin-top: 24px; }

/* Track Record Page 2 */
.tr-page2 { padding: 50px 40px; max-width: 1100px; margin: 0 auto; }

/* Buyer Profile & Objections */
.buyer-split { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; align-items: start; }
.buyer-split-left { }
.buyer-split-right { }
.obj-item { margin-bottom: 16px; }
.obj-q { font-weight: 700; color: #1B3A5C; margin-bottom: 4px; font-size: 14px; }
.obj-a { font-size: 13px; color: #444; line-height: 1.6; }
.bp-closing { font-size: 13px; color: #444; margin-top: 12px; font-style: italic; }
.buyer-photo { width: 100%; height: 220px; border-radius: 8px; overflow: hidden; margin-top: 24px; }
.buyer-photo img { width: 100%; height: 100%; object-fit: cover; }

/* Narrative paragraphs */
.narrative { font-size: 14px; line-height: 1.7; color: #444; margin-bottom: 16px; }

/* Maps (Google) */
.gmap { height: 400px; border-radius: 4px; border: 1px solid #ddd; margin-bottom: 30px; z-index: 1; }

/* Flyover hero video */
.cover-video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: brightness(0.5); opacity: 0; transition: opacity 1.8s ease; z-index: 1; }
.cover-video.live { opacity: 1; }
.video-attribution { position: absolute; bottom: 14px; right: 16px; z-index: 3; background: rgba(0,0,0,0.55); color: #fff; font-family: Roboto, Inter, sans-serif; font-size: 12px; font-weight: 400; padding: 4px 10px; border-radius: 4px; opacity: 0; transition: opacity 1.8s ease; }
.video-attribution.live { opacity: 1; }

/* Renovation section */
.reno-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0; }
.reno-grid img { width: 100%; height: 200px; object-fit: cover; border-radius: 6px; }
.reno-aerial { width: 100%; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.1); margin-bottom: 8px; }
.reno-aerial img { width: 100%; display: block; }
.aerial-caption { font-size: 12px; color: #888; margin-bottom: 24px; }
.map-fallback { display: none; }
.comp-map-print { display: none; }
.embed-map-wrap { position: relative; width: 100%; margin-bottom: 20px; border-radius: 8px; overflow: hidden; }
.embed-map-wrap iframe { display: block; width: 100%; height: 420px; border: 0; }

/* Misc */
.page-break-marker { height: 4px; background: repeating-linear-gradient(90deg, #ddd 0, #ddd 8px, transparent 8px, transparent 16px); }
.photo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 30px; overflow: hidden; }
.photo-grid img { width: 100%; height: 180px; object-fit: cover; border-radius: 4px; }
.highlight-box { background: #f0f4f8; border: 1px solid #dce3eb; border-radius: 8px; padding: 20px 24px; margin: 24px 0; }
.img-float-right { float: right; width: 48%; margin: 0 0 16px 20px; border-radius: 8px; overflow: hidden; }
.img-float-right img { width: 100%; display: block; }

/* Footer */
.footer { background: #1B3A5C; color: #fff; padding: 50px 40px; text-align: center; }
.footer-logo { width: 180px; margin-bottom: 30px; }
.footer-team { display: flex; justify-content: center; gap: 40px; margin-bottom: 30px; flex-wrap: wrap; }
.footer-person { text-align: center; flex: 1; min-width: 280px; }
.footer-headshot { width: 70px; height: 70px; border-radius: 50%; border: 2px solid #C5A258; object-fit: cover; }
.footer-name { font-size: 16px; font-weight: 600; }
.footer-title { font-size: 12px; color: #C5A258; margin-bottom: 8px; }
.footer-contact { font-size: 12px; color: rgba(255,255,255,0.7); line-height: 1.8; }
.footer-contact a { color: rgba(255,255,255,0.7); text-decoration: none; }
.footer-disclaimer { font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 20px; max-width: 800px; margin-left: auto; margin-right: auto; }
""")

# ============================================================
# MOBILE CSS (verbatim from blueprint)
# ============================================================
html_parts.append("""
@media (max-width: 768px) {
  .cover-content { padding: 30px 20px; }
  .cover-title { font-size: 32px; }
  .cover-logo { width: 220px; }
  .cover-headshots { gap: 24px; }
  .cover-headshot { width: 60px; height: 60px; }
  .section { padding: 30px 16px; }
  .photo-grid { grid-template-columns: 1fr; }
  .two-col, .buyer-split, .inv-split, .os-two-col, .loc-grid { grid-template-columns: 1fr; }
  .metrics-grid, .metrics-grid-4 { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .metric-card { padding: 14px 10px; }
  .metric-value { font-size: 22px; }
  .mkt-channels, .perf-grid { grid-template-columns: 1fr; }
  .summary-two-col, .prop-grid-4 { grid-template-columns: 1fr; }
  .pdf-float-btn { padding: 10px 18px; font-size: 12px; bottom: 16px; right: 16px; }
  .toc-nav { padding: 0 6px; }
  .toc-nav a { font-size: 10px; padding: 10px 6px; letter-spacing: 0.2px; }
  .gmap { height: 300px; }
  .reno-grid { grid-template-columns: 1fr 1fr; }
  .reno-grid img { height: 150px; }
  .embed-map-wrap iframe { height: 320px; }
  .loc-wide-map { height: 180px; margin-top: 16px; }
  .table-scroll table { min-width: 560px; }
  .bio-grid { grid-template-columns: 1fr; gap: 16px; }
  .bio-headshot { width: 60px; height: 60px; }
  .footer-team { flex-direction: column; align-items: center; }
  .press-strip { gap: 16px; }
  .press-logo { font-size: 11px; }
  .costar-badge-title { font-size: 18px; }
  .img-float-right { float: none; width: 100%; margin: 0 0 16px 0; }
  .inv-photo { height: 240px; }
}
@media (max-width: 420px) {
  .cover-title { font-size: 26px; }
  .cover-stat-value { font-size: 20px; }
  .cover-headshots { gap: 16px; }
  .cover-headshot { width: 50px; height: 50px; }
  .metrics-grid-4 { grid-template-columns: 1fr 1fr; }
  .metric-value { font-size: 18px; }
  .section { padding: 20px 12px; }
}
""")

# ============================================================
# PRINT CSS (verbatim from blueprint)
# ============================================================
html_parts.append("""
@media print {
  @page { size: letter landscape; margin: 0.4in 0.5in; }
  body { font-size: 11px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  p { font-size: 11px; line-height: 1.5; margin-bottom: 8px; }
  .pdf-float-btn, .toc-nav, .gmap, .embed-map-wrap, .page-break-marker, .map-fallback, .cover-video, .video-attribution { display: none !important; }
  .reno-grid { page-break-inside: avoid; }
  .reno-grid img { height: 150px; }
  #renovation { page-break-before: always; }
  .cover { min-height: 7.5in; page-break-after: always; }
  .cover-bg { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .cover-headshots { display: flex !important; }
  .cover-headshot { width: 55px; height: 55px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .cover-logo { width: 240px; }
  .section { padding: 20px 0; page-break-before: always; }
  .section-title { font-size: 20px; margin-bottom: 4px; }
  .section-subtitle { font-size: 11px; margin-bottom: 10px; }
  .section-divider { margin-bottom: 16px; }
  .metric-card { padding: 12px 8px; border-radius: 6px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .metric-value { font-size: 20px; }
  .metric-label { font-size: 9px; }
  table { font-size: 11px; }
  th { padding: 6px 8px; font-size: 9px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  td { padding: 5px 8px; }
  tr.highlight { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .tr-tagline { font-size: 15px; padding: 8px 14px; margin-bottom: 8px; }
  .tr-map-print { display: block; width: 100%; height: 240px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
  .tr-map-print img { width: 100%; height: 100%; object-fit: cover; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .tr-service-quote { margin: 10px 0; }
  .tr-service-quote h3 { font-size: 13px; margin-bottom: 4px; }
  .tr-service-quote p { font-size: 11px; line-height: 1.45; }
  .tr-page2 .section-title { font-size: 18px; margin-bottom: 2px; }
  .tr-page2 .section-divider { margin-bottom: 8px; }
  .bio-grid { gap: 12px; margin: 8px 0; }
  .bio-card { gap: 10px; }
  .bio-headshot { width: 75px; height: 75px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .bio-text { font-size: 11px; }
  .team-grid { gap: 6px; margin: 8px 0; }
  .team-headshot { width: 45px; height: 45px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .team-card-name { font-size: 11px; }
  .team-card-title { font-size: 9px; }
  .costar-badge { padding: 8px 12px; margin: 8px auto; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .costar-badge-title { font-size: 16px; }
  .condition-note { padding: 8px 14px; margin-top: 8px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .achievements-list { font-size: 11px; line-height: 1.5; }
  .press-strip { padding: 6px 12px; gap: 16px; margin-top: 8px; }
  .press-logo { font-size: 10px; }
  #marketing { page-break-before: always; }
  #marketing .section-title { font-size: 18px; margin-bottom: 2px; }
  #marketing .section-subtitle { font-size: 11px; margin-bottom: 4px; }
  #marketing .section-divider { margin-bottom: 6px; }
  #marketing .metrics-grid-4 { gap: 8px; margin-bottom: 8px; grid-template-columns: repeat(4, 1fr); }
  #marketing .metric-card { padding: 8px 6px; }
  #marketing .metric-value { font-size: 18px; }
  #marketing .metric-label { font-size: 8px; }
  .mkt-quote { padding: 8px 14px; margin: 8px 0; font-size: 11px; line-height: 1.4; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .mkt-channels { gap: 10px; margin-top: 8px; grid-template-columns: 1fr 1fr; }
  .mkt-channel { padding: 8px 12px; border-radius: 6px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .mkt-channel h4 { font-size: 11px; margin-bottom: 4px; }
  .mkt-channel li { font-size: 10px; line-height: 1.4; margin-bottom: 2px; }
  .perf-grid { gap: 10px; margin-top: 8px; grid-template-columns: 1fr 1fr; }
  .perf-card { padding: 8px 12px; border-radius: 6px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .perf-card h4 { font-size: 11px; margin-bottom: 4px; }
  .perf-card li { font-size: 10px; line-height: 1.4; margin-bottom: 2px; }
  .platform-strip { padding: 6px 12px; gap: 12px; margin-top: 8px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .platform-strip-label { font-size: 8px; }
  .platform-strip img { height: 18px; }
  .inv-text p { font-size: 11px; line-height: 1.5; margin-bottom: 6px; }
  .inv-logo { display: none !important; }
  .inv-right { padding-top: 30px; }
  .inv-photo { height: 220px; }
  .inv-photo img { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .inv-highlights { padding: 10px 14px; }
  .inv-highlights h4 { font-size: 11px; margin-bottom: 4px; }
  .inv-highlights li { font-size: 10px; line-height: 1.4; margin-bottom: 2px; }
  .loc-grid { display: grid; grid-template-columns: 58% 42%; gap: 14px; page-break-inside: avoid; }
  .loc-left { max-height: 340px; overflow: hidden; }
  .loc-left p { font-size: 10.5px; line-height: 1.4; margin-bottom: 5px; }
  .loc-right { max-height: 340px; overflow: hidden; }
  .loc-right table { font-size: 10px; }
  .loc-right th { font-size: 9px; padding: 4px 6px; }
  .loc-right td { padding: 4px 6px; font-size: 10px; }
  .loc-wide-map { height: 220px; margin-top: 8px; }
  .loc-wide-map img { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  #prop-details { page-break-before: always; }
  .prop-grid-4 { gap: 12px; }
  .prop-grid-4 table { font-size: 10px; }
  .prop-grid-4 th { font-size: 9px; padding: 4px 6px; }
  .prop-grid-4 td { padding: 4px 6px; font-size: 10px; }
  .os-two-col { page-break-before: always; align-items: stretch; gap: 16px; }
  .os-left table { font-size: 10px; }
  .os-left th { font-size: 9px; padding: 4px 6px; }
  .os-left td { padding: 4px 6px; }
  .os-right { font-size: 9.5px; line-height: 1.3; padding: 10px 12px; }
  .os-right p { margin-bottom: 4px; font-size: 9.5px; }
  .os-right .sub-heading { font-size: 12px; margin-bottom: 6px; }
  .summary-page { page-break-before: always; padding: 12px; }
  .summary-banner { font-size: 12px; padding: 6px 12px; margin-bottom: 10px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .summary-two-col { gap: 12px; }
  .summary-table { font-size: 8px; margin-bottom: 8px; }
  .summary-table td { padding: 2px 4px; }
  .summary-table th { padding: 2px 4px; }
  .summary-header { font-size: 7px !important; padding: 3px 4px !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .obj-q { font-size: 11px; margin-bottom: 2px; }
  .obj-a { font-size: 10px; line-height: 1.4; }
  .obj-item { margin-bottom: 8px; }
  .bp-closing { font-size: 10px; }
  .buyer-photo { height: 180px; }
  .buyer-photo img { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  #sale-comps, #on-market, #rent-comps { page-break-before: always; }
  .comp-narratives p.narrative { font-size: 10.5px; line-height: 1.4; margin-bottom: 6px; page-break-inside: avoid; }
  .comp-narratives p.narrative strong { font-size: 10.5px; }
  .comp-map-print { display: block !important; height: 280px; border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
  .comp-map-print img { width: 100%; height: 100%; object-fit: cover; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .tr-page2 { page-break-before: always; }
  .footer { page-break-before: always; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .footer-headshot { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .price-reveal { page-break-before: always; }
  #property-info { page-break-before: always; }

  /* --- Page-break discipline --- */
  p { orphans: 3; widows: 3; }
  table { page-break-inside: avoid; }
  .section-title, .section-subtitle, .section-divider { page-break-after: avoid; }
  .metrics-grid { page-break-inside: avoid; }
  .metric-card { page-break-inside: avoid; }
  .highlight-box { page-break-inside: avoid; }
  .obj-item { page-break-inside: avoid; }
  .bio-card { page-break-inside: avoid; }
  .inv-highlights { page-break-inside: avoid; }
  .photo-grid { page-break-inside: avoid; }
  .prop-grid-4 { page-break-inside: avoid; }
  .loc-grid { page-break-inside: avoid; }
  .feature-item { page-break-inside: avoid; }
  .mkt-channel { page-break-inside: avoid; }
  .perf-card { page-break-inside: avoid; }
  .team-grid { page-break-inside: avoid; }
  .costar-badge { page-break-inside: avoid; }
  .press-strip { page-break-inside: avoid; }
  .summary-two-col { page-break-inside: avoid; }
  #pdfOverlay { display: none !important; }
}
""")

# Close style and head
html_parts.append("</style>\n</head>\n<body>\n")

# ============================================================
# PAGE 1: COVER
# ============================================================
cover_headshots = ""
for agent in COVER_AGENTS:
    cover_headshots += f'''<div class="cover-headshot-wrap">
        <img class="cover-headshot" src="{IMG[agent['img_key']]}" alt="{agent['name']}">
        <div class="cover-headshot-name">{agent['name']}</div>
        <div class="cover-headshot-title">{agent['title']}</div>
    </div>\n'''

html_parts.append(f"""
<div class="cover">
  <div class="cover-bg" style="background-image:url('{IMG["hero"]}');"></div>
  <video class="cover-video" id="heroVideo" muted loop playsinline preload="none" poster=""></video>
  <div class="video-attribution" id="videoAttribution">Aerial imagery: Google</div>
  <div class="cover-content">
    <img src="{IMG['logo']}" class="cover-logo" alt="LAAA Team">
    <div class="cover-label">Confidential Broker Opinion of Value</div>
    <div class="cover-title">{ADDRESS}</div>
    <div class="cover-address">{CITY_STATE_ZIP}</div>
    <div class="cover-address" style="font-size:13px;margin-top:6px;color:#C5A258;">{PROPERTY_SUBTITLE}</div>
    <div class="gold-line" style="width:80px;margin:14px auto 24px;"></div>
    <div class="cover-stats">
      <div class="cover-stat"><span class="cover-stat-value">{UNITS}</span><span class="cover-stat-label">Units</span></div>
      <div class="cover-stat"><span class="cover-stat-value">&plusmn;{SF:,}</span><span class="cover-stat-label">Square Feet</span></div>
      <div class="cover-stat"><span class="cover-stat-value">{YEAR_BUILT}</span><span class="cover-stat-label">Year Built (Est.)</span></div>
      <div class="cover-stat"><span class="cover-stat-value">2026</span><span class="cover-stat-label">Renovated</span></div>
      <div class="cover-stat"><span class="cover-stat-value">{LOT_ACRES:.2f}</span><span class="cover-stat-label">Acres</span></div>
    </div>
    <div class="cover-headshots">
      {cover_headshots}
    </div>
    <p class="client-greeting" id="client-greeting">Prepared Exclusively for {CLIENT_NAME}</p>
    <p style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:8px;">{COVER_MONTH_YEAR}</p>
  </div>
</div>
""")

# ============================================================
# TOC NAV
# ============================================================
toc_links = '<a href="#track-record">Track Record</a>'
toc_links += '<a href="#marketing">Marketing</a>'
toc_links += '<a href="#investment">Investment</a>'
toc_links += '<a href="#location">Location</a>'
toc_links += '<a href="#renovation">Renovation</a>'
toc_links += '<a href="#floorplan">Floor Plan</a>'
toc_links += '<a href="#prop-details">Property</a>'
toc_links += '<a href="#property-info">Buyer Profile</a>'
toc_links += '<a href="#sale-comps">Sale Comps</a>'
if INCLUDE_ON_MARKET_COMPS:
    toc_links += '<a href="#on-market">On-Market</a>'
toc_links += '<a href="#rent-comps">Rent Comps</a>'
toc_links += '<a href="#financials">Financials</a>'
toc_links += '<a href="#contact">Contact</a>'

html_parts.append(f'<nav class="toc-nav" id="toc-nav">{toc_links}</nav>\n')

# ============================================================
# PAGE 2: TRACK RECORD P1
# ============================================================
html_parts.append(f"""
<div class="section section-alt" id="track-record">
  <div class="section-title">Team Track Record</div>
  <div class="section-subtitle">LA Apartment Advisors at Marcus &amp; Millichap</div>
  <div class="section-divider"></div>
  <div class="tr-tagline">
    <span style="display:block;font-size:1.2em;font-weight:700;margin-bottom:4px;">LAAA Team of Marcus &amp; Millichap</span>
    Expertise, Execution, Excellence.
  </div>
  <div class="metrics-grid-4">
    <div class="metric-card"><span class="metric-value">465</span><span class="metric-label">Closed Transactions</span></div>
    <div class="metric-card"><span class="metric-value">$1.47B</span><span class="metric-label">Total Sales Volume</span></div>
    <div class="metric-card"><span class="metric-value">4,216</span><span class="metric-label">Units Sold</span></div>
    <div class="metric-card"><span class="metric-value">34</span><span class="metric-label">Median DOM</span></div>
  </div>
  <div class="embed-map-wrap">
    <iframe src="https://www.google.com/maps/d/embed?mid=1ewCjzE3QX9p6m2MqK-md8b6fZitfIzU&ehbc=2E312F&noprof=1" loading="lazy" allowfullscreen></iframe>
  </div>
  <div class="tr-map-print"><img src="{IMG['closings_map']}" alt="LAAA Closings Map"></div>
  <div class="tr-service-quote">
    <h3>"We Didn't Invent Great Service, We Just Work Relentlessly to Provide It."</h3>
    <p>{MISSION_P1}</p>
    <p>{MISSION_P2}</p>
    <p>{MISSION_P3}</p>
  </div>
  <h3 class="sub-heading">Active on the Central Coast</h3>
  <div class="table-scroll"><table>
    <thead><tr><th>Property</th><th>City</th><th class="num">Units</th><th>Outcome</th></tr></thead>
    <tbody>
      <tr><td>514-516 E Oak St &amp; 601 Grand Ave</td><td>Ojai</td><td class="num">32</td><td>Sold 12/2025 | $8,250,000</td></tr>
      <tr><td>1200 N H St</td><td>Oxnard</td><td class="num">18</td><td>Sold twice by LAAA, most recently 05/2025</td></tr>
      <tr><td>40 N Brent St</td><td>Ventura</td><td class="num">8</td><td>Sold 02/2024 | $2,487,000</td></tr>
      <tr><td>318 S Voluntario St</td><td>Santa Barbara</td><td class="num">8</td><td>Sold twice by LAAA (2019 and 2021)</td></tr>
      <tr><td>6839 Sabado Tarde Rd</td><td>Goleta</td><td class="num">7</td><td>Sold 2021 | $635,000 per unit</td></tr>
      <tr><td>627 E Virginia Terrace</td><td>Santa Paula</td><td class="num">7</td><td>Sold 2020</td></tr>
      <tr style="background:#FFF8E7;"><td>180 Holly Ave</td><td>Carpinteria</td><td class="num">19</td><td>Active listing | $8,950,000</td></tr>
      <tr style="background:#FFF8E7;"><td>601 Pearl St</td><td>Ojai</td><td class="num">--</td><td>Active listing | development site</td></tr>
    </tbody>
  </table></div>
</div>
""")

# ============================================================
# PAGE 3: TRACK RECORD P2 (Our Team)
# ============================================================
# Team grid — all members except Glen and Filip (who get bio cards)
team_members = [
    ("Aida Memary Scher", "Associate", "team_aida"),
    ("Morgan Wetmore", "Associate", "team_morgan"),
    ("Luka Leader", "Associate", "team_luka"),
    ("Logan Ward", "Associate", "team_logan"),
    ("Alexandro Tapia", "Associate", "team_alexandro"),
    ("Blake Lewitt", "Associate", "team_blake"),
    ("Mike Palade", "Associate", "team_mike"),
    ("Tony H. Dang", "Associate", "team_tony"),
]

team_grid_html = ""
for name, title, img_key in team_members:
    team_grid_html += f'''<div class="team-card">
      <img class="team-headshot" src="{IMG[img_key]}" alt="{name}">
      <div class="team-card-name">{name}</div>
      <div class="team-card-title">{title}</div>
    </div>\n'''

# Glen and Filip bios — condensed from branding/team_bios.md (real personal bios)
GLEN_BIO = "Glen Scher is one of the top multifamily brokers in Los Angeles, with over 450 transactions and $1.4 billion in closed sales across LA and the Ventura and Santa Barbara counties. He is a Senior Managing Director at Marcus &amp; Millichap and co-founder of the LAAA Team, one of Southern California's most active multifamily brokerage groups, consistently closing 40+ deals per year. Chairman's Club, 2021."
FILIP_BIO = "Filip Niculete is one of Southern California's top commercial real estate brokers. Born in Romania and raised in the San Fernando Valley, he studied Finance at San Diego State and began his career at Marcus &amp; Millichap in 2011. He co-founded the LAAA Team, which leads the market in multifamily inventory, and has closed over $1.4 billion in transactions. Chairman's Club, 2021 and 2018."

html_parts.append(f"""
<div class="tr-page2">
  <div style="text-align:center;margin-bottom:8px;">
    <div class="section-title" style="margin-bottom:4px;">Our Team</div>
    <div class="section-divider" style="margin:0 auto 12px;"></div>
  </div>
  <div class="costar-badge" style="margin-top:4px;margin-bottom:8px;">
    <div class="costar-badge-title">#1 Most Active Multifamily Sales Team in LA County</div>
    <div class="costar-badge-sub">CoStar &bull; 2019, 2020, 2021 &bull; #4 in California</div>
  </div>
  <div class="bio-grid">
    <div class="bio-card">
      <img class="bio-headshot" src="{IMG['glen']}" alt="Glen Scher">
      <div>
        <div class="bio-name">Glen Scher</div>
        <div class="bio-title">Senior Managing Director</div>
        <div class="bio-text">{GLEN_BIO}</div>
      </div>
    </div>
    <div class="bio-card">
      <img class="bio-headshot" src="{IMG['filip']}" alt="Filip Niculete">
      <div>
        <div class="bio-name">Filip Niculete</div>
        <div class="bio-title">Senior Managing Director</div>
        <div class="bio-text">{FILIP_BIO}</div>
      </div>
    </div>
  </div>
  <div class="team-grid">
    {team_grid_html}
  </div>
  <div class="condition-note" style="margin-top:20px;">
    <div class="condition-note-label">Key Achievements</div>
    <p class="achievements-list">
      &bull; <strong>Chairman's Club</strong> - a top-tier annual honor at Marcus &amp; Millichap<br>
      &bull; <strong>National Achievement Award</strong> - Consistent top national performer<br>
      &bull; <strong>CoStar #1 Team</strong> - Most active multifamily sales team in LA County<br>
      &bull; <strong>465 Transactions</strong> - $1.47 billion in career sales volume<br>
      &bull; <strong>34-Day Median DOM</strong> - Properties sell faster than market average
    </p>
  </div>
  <div class="press-strip">
    <span class="press-strip-label">As Featured In</span>
    <span class="press-logo">BISNOW</span>
    <span class="press-logo">YAHOO FINANCE</span>
    <span class="press-logo">CONNECT CRE</span>
    <span class="press-logo">SFVBJ</span>
    <span class="press-logo">THE PINNACLE LIST</span>
  </div>
</div>
""")

# ============================================================
# PAGE 4: MARKETING & RESULTS (standard — same for every BOV)
# ============================================================
html_parts.append("""
<div class="page-break-marker"></div>
<div class="section" id="marketing">
  <div class="section-title">Our Marketing Approach &amp; Results</div>
  <div class="section-subtitle">Data-Driven Marketing + Proven Performance</div>
  <div class="section-divider"></div>
  <div class="metrics-grid-4">
    <div class="metric-card"><span class="metric-value">30K+</span><span class="metric-label">Targeted Emails</span></div>
    <div class="metric-card"><span class="metric-value">10K+</span><span class="metric-label">Listing Views</span></div>
    <div class="metric-card"><span class="metric-value">3.7</span><span class="metric-label">Avg Offers / Listing</span></div>
    <div class="metric-card"><span class="metric-value">18</span><span class="metric-label">Avg Days to Escrow</span></div>
  </div>
  <div class="mkt-quote">"We are PROACTIVE marketers, not reactive. Every listing gets a custom campaign designed to maximize exposure, create urgency, and drive competitive offers."</div>
  <div class="mkt-channels">
    <div class="mkt-channel"><h4>Direct Phone Outreach</h4><ul>
      <li>500+ targeted calls per listing</li>
      <li>Focus: active buyers in submarket</li>
      <li>Personal follow-up within 48 hours</li>
    </ul></div>
    <div class="mkt-channel"><h4>Email Campaigns</h4><ul>
      <li>30,000+ qualified investor contacts</li>
      <li>Segmented by geography and deal size</li>
      <li>Multi-touch drip campaigns</li>
    </ul></div>
    <div class="mkt-channel"><h4>Online Platforms</h4><ul>
      <li>MarcusMillichap.com, CoStar, Crexi</li>
      <li>LoopNet, CREXi, Ten-X</li>
      <li>Custom property websites</li>
    </ul></div>
    <div class="mkt-channel"><h4>Additional Channels</h4><ul>
      <li>Office-wide agent blast (100+ agents)</li>
      <li>Industry networking events</li>
      <li>Strategic broker co-marketing</li>
    </ul></div>
  </div>
  <div class="metrics-grid-4" style="margin-top:16px;">
    <div class="metric-card"><span class="metric-value">97.6%</span><span class="metric-label">Avg SP/LP Ratio</span></div>
    <div class="metric-card"><span class="metric-value">21%</span><span class="metric-label">Sold Above Ask</span></div>
    <div class="metric-card"><span class="metric-value">10</span><span class="metric-label">Avg Day Contingency</span></div>
    <div class="metric-card"><span class="metric-value">61%</span><span class="metric-label">1031 Exchange Buyers</span></div>
  </div>
  <div class="perf-grid">
    <div class="perf-card"><h4>Pricing Accuracy</h4><ul>
      <li>97.6% average sale-to-list ratio</li>
      <li>21% of listings sold above asking</li>
      <li>Data-driven comp analysis</li>
    </ul></div>
    <div class="perf-card"><h4>Marketing Speed</h4><ul>
      <li>18 average days to accepted offer</li>
      <li>34-day median days on market</li>
      <li>Strategic pricing drives urgency</li>
    </ul></div>
    <div class="perf-card"><h4>Contract Strength</h4><ul>
      <li>10-day average contingency period</li>
      <li>Pre-qualified buyer verification</li>
      <li>Streamlined due diligence process</li>
      <li>98% close rate on accepted offers</li>
    </ul></div>
    <div class="perf-card"><h4>Exchange Expertise</h4><ul>
      <li>61% of buyers are 1031 exchangers</li>
      <li>Dedicated exchange buyer database</li>
      <li>Timeline management expertise</li>
      <li>85% higher cash flow for exchangers</li>
    </ul></div>
  </div>
  <div class="platform-strip">
    <span class="platform-strip-label">Advertised On</span>
    <span class="platform-name">CREXI</span>
    <span class="platform-name">COSTAR</span>
    <span class="platform-name">LOOPNET</span>
    <span class="platform-name">ZILLOW</span>
    <span class="platform-name">REALTOR</span>
    <span class="platform-name">M&amp;M</span>
    <span class="platform-name">APARTMENTS.COM</span>
    <span class="platform-name">REDFIN</span>
    <span class="platform-name">TEN-X</span>
  </div>
</div>
""")

# ============================================================
# PAGE 5: INVESTMENT OVERVIEW
# ============================================================
highlights_html = ""
for bold, text in HIGHLIGHTS:
    highlights_html += f'<li><strong>{bold}</strong> - {text}</li>\n'

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="investment">
  <div class="section-title">Investment Overview</div>
  <div class="section-subtitle">{SUBMARKET} - {ADDRESS}</div>
  <div class="section-divider"></div>
  <div class="inv-split">
    <div class="inv-left">
      <div class="metrics-grid-4">
        <div class="metric-card"><span class="metric-value">{UNITS}</span><span class="metric-label">Units</span></div>
        <div class="metric-card"><span class="metric-value">{SF:,}</span><span class="metric-label">Square Feet</span></div>
        <div class="metric-card"><span class="metric-value">{YEAR_BUILT}</span><span class="metric-label">Year Built (Est.)</span></div>
        <div class="metric-card"><span class="metric-value">2026</span><span class="metric-label">Renovated</span></div>
      </div>
      <div class="inv-text">
        <p>{INVESTMENT_OVERVIEW_P1}</p>
        <p>{INVESTMENT_OVERVIEW_P2}</p>
        <p>{INVESTMENT_OVERVIEW_P3}</p>
      </div>
    </div>
    <div class="inv-right">
      <div class="inv-photo"><img src="{IMG['grid1']}" alt="Property"></div>
      <div class="inv-highlights">
        <h4>Investment Highlights</h4>
        <ul>
          {highlights_html}
        </ul>
      </div>
    </div>
  </div>
</div>
""")

# ============================================================
# PAGE 6: LOCATION OVERVIEW
# ============================================================
loc_table_rows = ""
for label, value in LOCATION_TABLE_ROWS:
    loc_table_rows += f'<tr><td>{label}</td><td>{value}</td></tr>\n'

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="location">
  <div class="section-title">Location Overview</div>
  <div class="section-subtitle">{SUBMARKET} - {CITY_STATE_ZIP.split(",")[1].strip() if "," in CITY_STATE_ZIP else CITY_STATE_ZIP}</div>
  <div class="section-divider"></div>
  <div class="reno-aerial"><img src="{IMG['hero']}" alt="124 Oceano Ave aerial, one row from Leadbetter Beach"></div>
  <p class="aerial-caption">124 Oceano Ave (outlined) one row from Leadbetter Beach, directly below Santa Barbara City College and the Great Meadow. Aerial imagery: Google.</p>
  <div class="loc-grid">
    <div class="loc-left">
      <p>{LOCATION_P1}</p>
      <p>{LOCATION_P2}</p>
      <p>{LOCATION_P3}</p>
    </div>
    <div class="loc-right">
      <table class="info-table">
        <thead><tr><th colspan="2">Location Details</th></tr></thead>
        <tbody>
          {loc_table_rows}
        </tbody>
      </table>
    </div>
  </div>
  <div class="loc-wide-map"><img src="{IMG['loc_map']}" alt="Location Map"></div>
</div>
""")

# ============================================================
# THE RENOVATION (custom section — gut-reno, delivered vacant)
# ============================================================
if INCLUDE_RENOVATION:
    html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="renovation">
  <div class="section-title">The Renovation</div>
  <div class="section-subtitle">Stud-Level Rebuild | Delivered Renovated &amp; 100% Vacant</div>
  <div class="section-divider"></div>
  <p class="narrative">The building is undergoing a comprehensive stud-level renovation completing in 2026. Interiors are being rebuilt with new flooring, paint, kitchens, baths, and finishes throughout, and the property will be delivered fully renovated and 100% vacant at close. The photos below show the current progression; final finished photography will follow completion.</p>
  <div class="reno-grid">
    <img src="{IMG['reno_ext']}" alt="Building exterior">
    <img src="{IMG['grid1']}" alt="Renovated living room">
    <img src="{IMG['reno_bed']}" alt="Renovated bedroom">
    <img src="{IMG['reno_room']}" alt="Renovated interior">
  </div>
  <div class="highlight-box">
    <h4 style="color:#1B3A5C;font-size:14px;margin-bottom:10px;">The Delivered-Vacant Advantage</h4>
    <ul style="font-size:13px;line-height:1.7;">
      <li><strong>Day-one market rents.</strong> Under Costa-Hawkins, initial rents on a vacant building are set by the buyer at full market, before Santa Barbara's permanent rent program arrives.</li>
      <li><strong>No inherited tenancies.</strong> No estoppels, no legacy rent schedules, no relocation exposure, and no surprises in the rent roll.</li>
      <li><strong>A clean ownership start.</strong> All-new interiors and finishes support lower near-term repair costs and a stronger insurance and financing profile than vintage coastal product.</li>
    </ul>
  </div>
  <div class="condition-note"><div class="condition-note-label">Buyer Verification</div>Renovation scope, permits, and final unit square footages are per ownership and should be independently verified during due diligence.</div>
</div>
""")

# ============================================================
# FLOOR PLAN (representative 2BD/2BA, Hover interior scan 2025-08-20)
# ============================================================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="floorplan">
  <div class="section-title">Representative Floor Plan</div>
  <div class="section-subtitle">Typical 2BD/2BA Unit | Measured Interior Scan</div>
  <div class="section-divider"></div>
  <p class="narrative">The typical 2-bedroom/2-bath plan was professionally scanned and measured in August 2025. Interior rooms total 638 SF: an open living and dining area of 246 SF, a 66 SF kitchen, bedrooms of 127 SF and 94 SF, two baths, and a connecting hallway. Including interior walls, the gross unit footprint is approximately 720 SF. The plan lives efficiently: two true bedrooms and two full baths in a footprint that keeps the building's rent per square foot at the top of the submarket.</p>
  <div style="background:#fff;border:1px solid #E0E0E0;border-radius:6px;padding:18px;margin:14px 0;text-align:center;">
    <img src="{IMG['floorplan']}" alt="Representative 2BD/2BA floor plan" style="max-width:100%;height:auto;">
  </div>
  <div class="condition-note"><div class="condition-note-label">Measurement Source</div>One representative 2-bedroom unit measured by Hover interior scan, August 2025. Remaining units are per owner plans. Buyer to verify all square footages during due diligence.</div>
</div>
""")

# ============================================================
# PAGE 7: PROPERTY DETAILS
# ============================================================
def build_info_table(title, rows, colspan=2):
    html = f'<table class="info-table"><thead><tr><th colspan="{colspan}">{title}</th></tr></thead><tbody>\n'
    for row in rows:
        if len(row) == 2:
            html += f'<tr><td>{row[0]}</td><td>{row[1]}</td></tr>\n'
        elif len(row) == 3:
            html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>\n'
    html += '</tbody></table>\n'
    return html

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="prop-details">
  <div class="section-title">Property Details</div>
  <div class="section-subtitle">{FULL_ADDRESS}</div>
  <div class="section-divider"></div>
  <div class="prop-grid-4">
    <div>{build_info_table("Property Overview", PROP_OVERVIEW)}</div>
    <div>{build_info_table("Site &amp; Zoning", PROP_SITE_ZONING)}</div>
    <div>{build_info_table("Building Systems &amp; Capital Improvements", PROP_BUILDING, 3)}</div>
    <div>{build_info_table("Regulatory &amp; Compliance", PROP_REGULATORY)}</div>
  </div>
</div>
""")

# ============================================================
# OPTIONAL: TRANSACTION HISTORY
# ============================================================
if INCLUDE_TRANSACTION_HISTORY and TRANSACTION_ROWS:
    tx_rows_html = ""
    for tx in TRANSACTION_ROWS:
        tx_rows_html += f'<tr><td>{tx.get("date","")}</td><td>{tx.get("parties","")}</td><td class="num">{fc(tx.get("price",0))}</td><td class="num">{fc(tx.get("ppu",0))}</td><td class="num">{fc(tx.get("psf",0))}</td><td>{tx.get("notes","")}</td></tr>\n'
    html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="transactions">
  <div class="section-title">Transaction History</div>
  <div class="section-subtitle">Ownership &amp; Sale Record</div>
  <div class="section-divider"></div>
  <div class="table-scroll"><table>
    <thead><tr><th>Date</th><th>Grantor / Grantee</th><th class="num">Sale Price</th><th class="num">$/Unit</th><th class="num">$/SF</th><th>Notes</th></tr></thead>
    <tbody>{tx_rows_html}</tbody>
  </table></div>
  <p>{TRANSACTION_NARRATIVE}</p>
</div>
""")

# ============================================================
# PAGE 8: BUYER PROFILE & OBJECTIONS
# ============================================================
buyer_types_html = ""
for btype, desc in BUYER_TYPES:
    buyer_types_html += f'''<div class="obj-item">
        <p class="obj-q">{btype}</p>
        <p class="obj-a">{desc}</p>
    </div>\n'''

buyer_obj_html = ""
for question, answer in BUYER_OBJECTIONS:
    buyer_obj_html += f'''<div class="obj-item">
        <p class="obj-q">"{question}"</p>
        <p class="obj-a">{answer}</p>
    </div>\n'''

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="property-info">
  <div class="section-title">Buyer Profile &amp; Anticipated Objections</div>
  <div class="section-subtitle">Target Investors &amp; Data-Backed Responses</div>
  <div class="section-divider"></div>
  <div class="buyer-split">
    <div class="buyer-split-left">
      <h3 class="sub-heading">Target Buyer Profile</h3>
      {buyer_types_html}
      <p class="bp-closing">{BUYER_CLOSING}</p>
    </div>
    <div class="buyer-split-right">
      <h3 class="sub-heading">Anticipated Buyer Objections</h3>
      {buyer_obj_html}
    </div>
  </div>
  <div class="buyer-photo"><img src="{IMG['buyer_photo']}" alt="Property"></div>
</div>
""")

# ============================================================
# PAGES 9-11: COMP SECTIONS
# ============================================================

# Sale Comps
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="sale-comps">
  <div class="section-title">Comparable Sales</div>
  <div class="section-subtitle">Closed Multifamily Transactions</div>
  <div class="section-divider"></div>
  <div class="gmap" id="saleMap"></div>
  <div class="comp-map-print"><img src="{IMG['sale_map_static']}" alt="Sale Comps Map"></div>
  <div class="table-scroll"><table>
    <thead><tr><th>#</th><th>Address</th><th class="num">Units</th><th>Year</th><th class="num">SF</th><th class="num">Price</th><th class="num">$/Unit</th><th class="num">$/SF</th><th class="num">Cap</th><th class="num">GRM</th><th>Date</th><th class="num">DOM</th></tr></thead>
    <tbody>{sale_comp_html}</tbody>
  </table></div>
  <div class="comp-narratives">
    {COMP_NARRATIVES}
  </div>
</div>
""")

# On-Market Comps (conditional)
if INCLUDE_ON_MARKET_COMPS:
    html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="on-market">
  <div class="section-title">Active Competition</div>
  <div class="section-subtitle">On-Market Renovated Coastal Product</div>
  <div class="section-divider"></div>
  <div class="table-scroll"><table>
    <thead><tr><th>#</th><th>Address</th><th class="num">Units</th><th>Year</th><th class="num">SF</th><th class="num">Price</th><th class="num">$/Unit</th><th class="num">$/SF</th><th class="num">DOM</th><th>Notes</th></tr></thead>
    <tbody>{on_market_html}</tbody>
  </table></div>
  <div class="comp-narratives"><p class="narrative">{ON_MARKET_NARRATIVE}</p></div>
</div>
""")

# Rent Comps
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="rent-comps">
  <div class="section-title">Rent Comparables</div>
  <div class="section-subtitle">Active Rental Listings in Submarket</div>
  <div class="section-divider"></div>
  <div class="gmap" id="rentMap"></div>
  <div class="comp-map-print"><img src="{IMG['rent_map_static']}" alt="Rent Comps Map"></div>
  <div class="table-scroll"><table>
    <thead><tr><th>#</th><th>Address</th><th>Type</th><th class="num">SF</th><th class="num">Rent</th><th class="num">$/SF</th><th>Source</th></tr></thead>
    <tbody>{rent_comp_html}</tbody>
  </table></div>
</div>
""")

# ============================================================
# PAGE 12: FINANCIAL ANALYSIS — RENT ROLL
# ============================================================
if PROPERTY_TYPE == "value-add":
    rr_header = '<thead><tr><th>Unit</th><th>Type</th><th class="num">SF</th><th class="num">Current Rent</th><th class="num">Rent/SF</th><th class="num">Market Rent</th><th class="num">Market/SF</th></tr></thead>'
else:
    rr_header = '<thead><tr><th>Unit</th><th>Type</th><th class="num">SF</th><th class="num">Rent/Mo</th><th class="num">Rent/SF</th><th>Status</th><th>Notes</th></tr></thead>'

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="financials">
  <div class="section-title">Financial Analysis</div>
  <div class="section-subtitle">Investment Underwriting</div>
  <div class="section-divider"></div>
  <h3 class="sub-heading">Unit Mix &amp; Rent Roll</h3>
  <div class="table-scroll"><table>
    {rr_header}
    <tbody>{rent_roll_html}</tbody>
  </table></div>
""")

# ============================================================
# PAGE 13: OPERATING STATEMENT + NOTES
# ============================================================
html_parts.append(f"""
  <div class="os-two-col">
    <div class="os-left">
      <h3 class="sub-heading">Operating Statement</h3>
      <table>
        <thead><tr><th>Income</th><th class="num">Annual</th><th class="num">Per Unit</th><th class="num">$/SF</th><th class="num">% EGI</th></tr></thead>
        <tbody>{os_income_html}</tbody>
      </table>
      <table>
        <thead><tr><th>Expenses</th><th class="num">Annual</th><th class="num">Per Unit</th><th class="num">$/SF</th><th class="num">% EGI</th></tr></thead>
        <tbody>{os_expense_html}</tbody>
      </table>
    </div>
    <div class="os-right">
      <h3 class="sub-heading">Notes to Operating Statement</h3>
      {os_notes_html}
    </div>
  </div>
""")

# ============================================================
# PAGE 14: FINANCIAL SUMMARY
# ============================================================
m = AT_LIST
down_pct = m["down_payment"] / m["price"] * 100 if m["price"] > 0 else 0

if PROPERTY_TYPE == "value-add":
    returns_label_1, returns_label_2 = "Current", "Pro Forma"
else:
    returns_label_1, returns_label_2 = "Reassessed", ""

html_parts.append(f"""
  <div class="summary-page">
    <div class="summary-banner">Summary</div>
    <div class="summary-two-col">
      <div class="summary-left">
        <table class="summary-table">
          <thead><tr><th colspan="2" class="summary-header">OPERATING DATA</th></tr></thead>
          <tbody>
            <tr><td>Price</td><td class="num">${LIST_PRICE:,}</td></tr>
            <tr><td>Down Payment ({down_pct:.0f}%)</td><td class="num">${m['down_payment']:,.0f}</td></tr>
            <tr><td>Number of Units</td><td class="num">{UNITS}</td></tr>
            <tr><td>Price / Unit</td><td class="num">${m['per_unit']:,.0f}</td></tr>
            <tr><td>Price / SF</td><td class="num">${m['per_sf']:,.0f}</td></tr>
            <tr><td>Gross SF</td><td class="num">{SF:,}</td></tr>
            <tr><td>Lot Size</td><td class="num">{LOT_SF:,} SF ({LOT_ACRES:.2f} ac)</td></tr>
            <tr><td>Year Built (Est.)</td><td class="num">{YEAR_BUILT}</td></tr>
            <tr><td>Renovated</td><td class="num">2026</td></tr>
          </tbody>
        </table>
        <table class="summary-table">
          <thead><tr><th class="summary-header">Returns</th><th class="summary-header num">{returns_label_1}</th>{"<th class='summary-header num'>" + returns_label_2 + "</th>" if returns_label_2 else ""}</tr></thead>
          <tbody>
            <tr><td>Cap Rate</td><td class="num">{m['cur_cap']:.2f}%</td>{"<td class='num'>" + f"{m['pf_cap']:.2f}%" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>GRM</td><td class="num">{m['grm']:.2f}x</td>{"<td class='num'>" + f"{m['pf_grm']:.2f}x" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>Cash-on-Cash</td><td class="num">{m['coc_cur']:.2f}%</td>{"<td class='num'>" + f"{m['coc_pf']:.2f}%" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>DSCR</td><td class="num">{m['dcr_cur']:.2f}x</td>{"<td class='num'>" + f"{m['dcr_pf']:.2f}x" + "</td>" if returns_label_2 else ""}</tr>
          </tbody>
        </table>
        <table class="summary-table">
          <thead><tr><th colspan="2" class="summary-header">FINANCING</th></tr></thead>
          <tbody>
            <tr><td>Loan Amount</td><td class="num">${m['loan_amount']:,.0f}</td></tr>
            <tr><td>Loan Type</td><td class="num">Fixed</td></tr>
            <tr><td>Interest Rate</td><td class="num">{INTEREST_RATE*100:.2f}%</td></tr>
            <tr><td>Amortization</td><td class="num">{AMORTIZATION_YEARS} Years</td></tr>
            <tr><td>Loan Constant</td><td class="num">{LOAN_CONSTANT*100:.2f}%</td></tr>
            <tr><td>LTV ({m['loan_constraint']})</td><td class="num">{m['actual_ltv']*100:.1f}%</td></tr>
            <tr><td>DSCR</td><td class="num">{m['dcr_cur']:.2f}x</td></tr>
          </tbody>
        </table>
      </div>
      <div class="summary-right">
        <table class="summary-table">
          <thead><tr><th class="summary-header">Income</th><th class="summary-header num">{returns_label_1}</th>{"<th class='summary-header num'>" + returns_label_2 + "</th>" if returns_label_2 else ""}</tr></thead>
          <tbody>
            <tr><td>GSR</td><td class="num">${GSR:,}</td>{"<td class='num'>$" + f"{PF_GSR:,}" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>Vacancy ({VACANCY_PCT*100:.0f}%)</td><td class="num">$({GSR*VACANCY_PCT:,.0f})</td>{"<td class='num'>$(" + f"{PF_GSR*VACANCY_PCT:,.0f}" + ")</td>" if returns_label_2 else ""}</tr>
            <tr><td>Other Income</td><td class="num">${OTHER_INCOME:,}</td>{"<td class='num'>$" + f"{OTHER_INCOME:,}" + "</td>" if returns_label_2 else ""}</tr>
            <tr class="summary"><td><strong>EGI</strong></td><td class="num"><strong>${m['cur_egi']:,.0f}</strong></td>{"<td class='num'><strong>$" + f"{m['pf_egi']:,.0f}" + "</strong></td>" if returns_label_2 else ""}</tr>
          </tbody>
        </table>
        <table class="summary-table">
          <thead><tr><th class="summary-header">Cash Flow</th><th class="summary-header num">{returns_label_1}</th>{"<th class='summary-header num'>" + returns_label_2 + "</th>" if returns_label_2 else ""}</tr></thead>
          <tbody>
            <tr><td>NOI</td><td class="num">${m['cur_noi']:,.0f}</td>{"<td class='num'>$" + f"{m['pf_noi']:,.0f}" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>Debt Service</td><td class="num">$({m['debt_service']:,.0f})</td>{"<td class='num'>$(" + f"{m['debt_service']:,.0f}" + ")</td>" if returns_label_2 else ""}</tr>
            <tr class="summary"><td><strong>Net Cash Flow</strong></td><td class="num"><strong>${m['net_cf_cur']:,.0f}</strong></td>{"<td class='num'><strong>$" + f"{m['net_cf_pf']:,.0f}" + "</strong></td>" if returns_label_2 else ""}</tr>
            <tr><td>CoC Return</td><td class="num">{m['coc_cur']:.2f}%</td>{"<td class='num'>" + f"{m['coc_pf']:.2f}%" + "</td>" if returns_label_2 else ""}</tr>
            <tr><td>Principal Reduction</td><td class="num">${m['prin_red']:,.0f}</td>{"<td class='num'>$" + f"{m['prin_red']:,.0f}" + "</td>" if returns_label_2 else ""}</tr>
            <tr class="summary"><td><strong>Total Return</strong></td><td class="num"><strong>{m['total_return_pct_cur']:.2f}%</strong></td>{"<td class='num'><strong>" + f"{m['total_return_pct_pf']:.2f}%" + "</strong></td>" if returns_label_2 else ""}</tr>
          </tbody>
        </table>
        <table class="summary-table">
          <thead><tr><th colspan="2" class="summary-header">EXPENSES</th></tr></thead>
          <tbody>
            {sum_expense_html}
            <tr class="summary"><td><strong>Total Expenses</strong></td><td class="num"><strong>${total_exp_calc:,.0f}</strong></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
""")

# ============================================================
# PAGE 15: PRICE REVEAL + PRICING MATRIX
# ============================================================
if PROPERTY_TYPE == "value-add":
    matrix_header = '<thead><tr><th class="num">Purchase Price</th><th class="num">Current Cap</th><th class="num">Pro Forma Cap</th><th class="num">Cash-on-Cash</th><th class="num">$/SF</th><th class="num">$/Unit</th><th class="num">PF GRM</th></tr></thead>'
else:
    matrix_header = '<thead><tr><th class="num">Purchase Price</th><th class="num">Cap Rate</th><th class="num">Cash-on-Cash</th><th class="num">$/Unit</th><th class="num">$/SF</th><th class="num">GRM</th><th class="num">DSCR</th></tr></thead>'

html_parts.append(f"""
  <div class="price-reveal">
    <div style="text-align:center;margin-bottom:32px;">
      <div style="font-size:13px;text-transform:uppercase;letter-spacing:2px;color:#C5A258;font-weight:600;margin-bottom:8px;">Suggested List Price</div>
      <div style="font-size:56px;font-weight:700;color:#1B3A5C;line-height:1;">${LIST_PRICE:,}</div>
    </div>
    <div class="metrics-grid metrics-grid-4">
      <div class="metric-card"><span class="metric-value">${m['per_unit']:,.0f}</span><span class="metric-label">Price / Unit</span></div>
      <div class="metric-card"><span class="metric-value">${m['per_sf']:,.0f}</span><span class="metric-label">Price / SF</span></div>
      <div class="metric-card"><span class="metric-value">{m['cur_cap']:.2f}%</span><span class="metric-label">Current Cap Rate</span></div>
      <div class="metric-card"><span class="metric-value">{m['grm']:.2f}x</span><span class="metric-label">Current GRM</span></div>
    </div>
    <h3 class="sub-heading">Pricing Matrix</h3>
    <div class="table-scroll"><table>
      {matrix_header}
      <tbody>{matrix_html}</tbody>
    </table></div>
    <div class="summary-trade-range">
      <div class="summary-trade-label">A TRADE PRICE IN THE CURRENT INVESTMENT ENVIRONMENT OF</div>
      <div class="summary-trade-prices">${TRADE_RANGE_LOW:,} to ${TRADE_RANGE_HIGH:,}</div>
    </div>
    <h3 class="sub-heading">Pricing Rationale</h3>
    <p>{PRICING_RATIONALE}</p>
    <div class="condition-note"><strong>Assumptions &amp; Conditions:</strong> {ASSUMPTIONS_DISCLAIMER}</div>
  </div>
</div>
""")

# ============================================================
# PAGE 16: FOOTER
# ============================================================
footer_agents_html = ""
for agent in FOOTER_AGENTS:
    footer_agents_html += f'''<div class="footer-person">
      <img src="{IMG[agent['img_key']]}" class="footer-headshot" alt="{agent['name']}">
      <div class="footer-name">{agent['name']}</div>
      <div class="footer-title">{agent['title']}</div>
      <div class="footer-contact">
        <a href="tel:{agent['phone']}">{agent['phone']}</a><br>
        <a href="mailto:{agent['email']}">{agent['email']}</a><br>
        CA License: {agent['license']}
      </div>
    </div>\n'''

html_parts.append(f"""
<div class="footer" id="contact">
  <img src="{IMG['logo']}" class="footer-logo" alt="LAAA Team">
  <div class="footer-team">
    {footer_agents_html}
  </div>
  <div class="footer-office">16830 Ventura Blvd, Ste. 100, Encino, CA 91436 | marcusmillichap.com/laaa-team</div>
  <div class="footer-disclaimer">This information has been secured from sources we believe to be reliable, but we make no representations or warranties, expressed or implied, as to the accuracy of the information. Buyer must verify the information and bears all risk for any inaccuracies. Marcus &amp; Millichap Real Estate Investment Services, Inc. | License: CA 01930580.</div>
</div>
""")

# PDF Download Button
html_parts.append(f"""
<a href="{PDF_LINK}" class="pdf-float-btn" id="pdfBtn" target="_blank">
  <svg viewBox="0 0 24 24"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12,19L8,15H10.5V12H13.5V15H16L12,19Z"/></svg>
  Download PDF
</a>
<div id="pdfOverlay" style="display:none;position:fixed;inset:0;background:rgba(27,58,92,0.85);z-index:99999;justify-content:center;align-items:center;flex-direction:column;gap:12px;">
  <div style="width:48px;height:48px;border:4px solid rgba(197,162,88,0.3);border-top-color:#C5A258;border-radius:50%;animation:pdfSpin 0.8s linear infinite;"></div>
  <div style="color:#fff;font-size:20px;font-weight:700;letter-spacing:0.5px;">Generating PDF</div>
  <div style="color:#C5A258;font-size:13px;">This typically takes 15 to 30 seconds. A new tab will open with your download.</div>
</div>
<style>@keyframes pdfSpin {{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}</style>
""")

# ============================================================
# JAVASCRIPT
# ============================================================
html_parts.append(f"""
<script>
// Client personalization
var params = new URLSearchParams(window.location.search);
var client = params.get('client');
if (client) {{
  var el = document.getElementById('client-greeting');
  if (el) el.textContent = 'Prepared Exclusively for ' + client;
}}

// TOC smooth scroll
document.querySelectorAll('.toc-nav a').forEach(function(link) {{
  link.addEventListener('click', function(e) {{
    e.preventDefault();
    var target = document.querySelector(this.getAttribute('href'));
    if (target) {{
      var navHeight = document.getElementById('toc-nav').offsetHeight;
      window.scrollTo({{ top: target.getBoundingClientRect().top + window.pageYOffset - navHeight - 4, behavior: 'smooth' }});
    }}
  }});
}});

// Active TOC highlighting
var tocLinks = document.querySelectorAll('.toc-nav a');
var tocSections = [];
tocLinks.forEach(function(link) {{
  var section = document.getElementById(link.getAttribute('href').substring(1));
  if (section) tocSections.push({{ link: link, section: section }});
}});
function updateActiveTocLink() {{
  var navHeight = document.getElementById('toc-nav').offsetHeight + 20;
  var scrollPos = window.pageYOffset + navHeight;
  var current = null;
  tocSections.forEach(function(item) {{ if (item.section.offsetTop <= scrollPos) current = item.link; }});
  tocLinks.forEach(function(link) {{ link.classList.remove('toc-active'); }});
  if (current) current.classList.add('toc-active');
}}
window.addEventListener('scroll', updateActiveTocLink);
updateActiveTocLink();

// PDF button loading overlay
var pdfBtn = document.getElementById('pdfBtn');
var pdfOverlay = document.getElementById('pdfOverlay');
if (pdfBtn && pdfOverlay) {{
  pdfBtn.addEventListener('click', function() {{
    pdfOverlay.style.display = 'flex';
    setTimeout(function() {{ pdfOverlay.style.display = 'none'; }}, 8000);
  }});
}}

// Google Maps init (called by the Maps JS loader below)
function initMaps() {{
{sale_map_js}
{active_map_js}
{rent_map_js}
}}
window.initMaps = initMaps;

// Aerial View flyover: fetch a fresh stream URI on each load (Google policy: URIs expire,
// videos may not be cached or self-hosted). Image hero stays if anything fails.
(function() {{
  var video = document.getElementById('heroVideo');
  var attribution = document.getElementById('videoAttribution');
  if (!video) return;
  fetch('https://aerialview.googleapis.com/v1/videos:lookupVideo?videoId={AERIAL_VIDEO_ID}&key={MAPS_BROWSER_KEY}')
    .then(function(r) {{ if (!r.ok) throw new Error('lookup ' + r.status); return r.json(); }})
    .then(function(data) {{
      if (data.state !== 'ACTIVE' || !data.uris) throw new Error('video not active');
      var mp4 = (data.uris.MP4_MEDIUM && data.uris.MP4_MEDIUM.landscapeUri) ||
                (data.uris.MP4_HIGH && data.uris.MP4_HIGH.landscapeUri) ||
                (data.uris.MP4_LOW && data.uris.MP4_LOW.landscapeUri);
      if (!mp4) throw new Error('no mp4 uri');
      video.src = mp4;
      video.addEventListener('canplay', function() {{
        video.play().then(function() {{
          video.classList.add('live');
          if (attribution) attribution.classList.add('live');
        }}).catch(function() {{}});
      }}, {{ once: true }});
      video.load();
    }})
    .catch(function(e) {{ /* image hero remains */ }});
}})();
</script>
<script async src="https://maps.googleapis.com/maps/api/js?key={MAPS_BROWSER_KEY}&callback=initMaps"></script>
</body>
</html>
""")

# ============================================================
# WRITE OUTPUT FILE
# ============================================================
print(f"\nAssembling HTML...")
html = "".join(html_parts)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)
file_size = os.path.getsize(OUTPUT)
print(f"Done! Wrote {OUTPUT}")
print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
print(f"URL: {BOV_BASE_URL}")
