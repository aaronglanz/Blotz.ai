"""Property24 scraper for targeted Cape Town residential rental listings.

Fetches listing data from selected Property24 suburb search result pages and
individual listing pages, returning normalized listings ready for upsert into
cached_listings.

The goal is not to scrape all of Cape Town. For the MVP, we only want useful
residential listings in target suburbs.
"""

import logging
import re
import time
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

BASE_URL = "https://www.property24.com"

# Edit this list as your MVP focus changes.
# These slugs are based on the Property24 URL format:
# /to-rent/{suburb-slug}/cape-town/western-cape/{area-id}
#
# If one URL returns 404 or zero listings, go to Property24 in the browser,
# search the suburb manually, and copy the final URL into this dict.
TARGET_SUBURB_URLS: dict[str, str] = {
    "Sea Point": f"{BASE_URL}/to-rent/sea-point/cape-town/western-cape/11021",
    "Green Point": f"{BASE_URL}/to-rent/green-point/cape-town/western-cape/11017",
    "Mouille Point": f"{BASE_URL}/to-rent/mouille-point/cape-town/western-cape/11019",
    "Gardens": f"{BASE_URL}/to-rent/gardens/cape-town/western-cape/10164",
    "Vredehoek": f"{BASE_URL}/to-rent/vredehoek/cape-town/western-cape/10169",
    "Tamboerskloof": f"{BASE_URL}/to-rent/tamboerskloof/cape-town/western-cape/10167",
    "Claremont": f"{BASE_URL}/to-rent/claremont/cape-town/western-cape/9976",
    "Rondebosch": f"{BASE_URL}/to-rent/rondebosch/cape-town/western-cape/10163",
    "Newlands": f"{BASE_URL}/to-rent/newlands/cape-town/western-cape/10013",
    "Observatory": f"{BASE_URL}/to-rent/observatory/cape-town/western-cape/10157",
    "Woodstock": f"{BASE_URL}/to-rent/woodstock/cape-town/western-cape/10172",
}

# Only keep normal residential rentals.
# Exclude commercial, retail, industrial, farms, offices, vacant land, etc.
RESIDENTIAL_PROPERTY_TYPES = {
    "apartment",
    "flat",
    "house",
    "townhouse",
    "penthouse",
    "cottage",
    "studio",
    "duplex",
    "loft",
    "garden cottage",
    "room",
}

NON_RESIDENTIAL_KEYWORDS = {
    "commercial",
    "office",
    "retail",
    "industrial",
    "warehouse",
    "factory",
    "shop",
    "showroom",
    "business",
    "farm",
    "smallholding",
    "vacant land",
    "land",
    "plot",
    "storage",
}

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
}


@dataclass
class ScrapedListing:
    source: str
    source_url: str
    source_id: str | None
    title: str
    location: str
    suburb: str | None
    price_amount: int | None
    price_display: str
    bedrooms: int | None
    bathrooms: int | None
    size_sqm: int | None
    property_type: str | None
    description: str | None
    image_url: str | None
    image_urls: list[str]
    contact_name: str | None
    contact_phone: str | None


def _parse_price(text: str) -> tuple[int | None, str]:
    """Extract numeric price in rands and display string from price text."""
    display = text.strip()
    match = re.search(r"R\s*([\d\s,]+)", display)
    if match:
        num_str = match.group(1).replace(" ", "").replace(",", "")
        try:
            return int(num_str), display
        except ValueError:
            pass
    return None, display


def _parse_int(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _extract_listing_id(url: str) -> str | None:
    """Extract the Property24 listing ID from a URL like /to-rent/.../12345678."""
    match = re.search(r"/(\d{6,})", url)
    return match.group(1) if match else None


def _get_client(referer: str | None = None) -> httpx.Client:
    import random

    headers = {
        **HEADERS,
        "User-Agent": random.choice(USER_AGENTS),
    }

    if referer:
        headers["Referer"] = referer

    return httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers=headers,
    )


def _get_session(referer: str | None = None) -> httpx.Client:
    """Create a persistent session that mimics a browser.

    Visits a search page first to collect cookies before hitting detail pages.
    """
    import random

    warmup_url = referer or next(iter(TARGET_SUBURB_URLS.values()))

    client = httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers={
            **HEADERS,
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": warmup_url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        },
    )

    try:
        client.get(warmup_url)
    except Exception:
        pass

    return client


def _is_residential_listing(listing: ScrapedListing) -> bool:
    """Return True only for residential rental listings."""
    title = (listing.title or "").lower()
    ptype = (listing.property_type or "").lower()

    combined = f"{title} {ptype}"

    if any(keyword in combined for keyword in NON_RESIDENTIAL_KEYWORDS):
        return False

    # If we confidently parsed a residential property type, keep it.
    if ptype in RESIDENTIAL_PROPERTY_TYPES:
        return True

    # If no type was parsed, infer from residential title words.
    if any(keyword in title for keyword in RESIDENTIAL_PROPERTY_TYPES):
        return True

    return False


def scrape_search_page(
    page: int = 1,
    search_url: str | None = None,
    expected_suburb: str | None = None,
) -> list[ScrapedListing]:
    """Scrape a single Property24 rental search result page."""
    base_search_url = search_url or next(iter(TARGET_SUBURB_URLS.values()))
    url = base_search_url if page == 1 else f"{base_search_url}/p{page}"

    logger.info(
        f"Scraping Property24 page {page}"
        f"{f' for {expected_suburb}' if expected_suburb else ''}: {url}"
    )

    with _get_client(referer=base_search_url) as client:
        resp = client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    listings: list[ScrapedListing] = []

    tiles = soup.select(".js_resultTile")

    for tile in tiles:
        try:
            listing = _parse_tile(tile, expected_suburb=expected_suburb)
            if not listing:
                continue

            if not _is_residential_listing(listing):
                logger.debug(f"Skipping non-residential listing: {listing.title}")
                continue

            listings.append(listing)

        except Exception:
            logger.debug("Failed to parse tile", exc_info=True)
            continue

    logger.info(
        f"Page {page}"
        f"{f' for {expected_suburb}' if expected_suburb else ''}: "
        f"found {len(listings)} residential listings"
    )

    return listings


def _parse_tile(tile: Tag, expected_suburb: str | None = None) -> ScrapedListing | None:
    """Parse a single listing tile from search results."""
    link = tile.select_one("a[href*='/to-rent/']")
    if not link or not link.get("href"):
        return None

    href = link["href"]
    if not href.startswith("http"):
        href = BASE_URL + href

    source_id = _extract_listing_id(href)
    if not source_id:
        return None

    desc_el = tile.select_one(".p24_description")
    loc_el = tile.select_one(".p24_location")

    desc_text = desc_el.get_text(strip=True) if desc_el else ""
    location = loc_el.get_text(strip=True) if loc_el else ""

    title = desc_text.rstrip()
    title = re.sub(r"\bin([A-Z])", r"in \1", title)

    if title.endswith(" in") and location:
        title = f"{title} {location}"
    elif location and location not in title:
        title = f"{title} - {location}"

    if not title or len(title) < 5:
        return None

    suburb = expected_suburb or location.strip() or None
    location = location or expected_suburb or "Cape Town"

    price_el = tile.select_one(".p24_price")
    price_text = ""
    if price_el:
        price_text = "".join(
            child for child in price_el.children if isinstance(child, str)
        ).strip()

    price_amount, price_display = (
        _parse_price(price_text) if price_text else (None, "POA")
    )

    feature_spans = tile.select(".p24_featureDetails")
    beds = None
    baths = None
    size = None

    for span in feature_spans:
        text = span.get_text(strip=True)

        if "m²" in text:
            size = _parse_int(text)
            continue

        prev = span.find_previous_sibling()
        if prev and prev.name == "svg":
            svg_classes = " ".join(prev.get("class", []))
            if "bedroom" in svg_classes.lower() or "bed" in svg_classes.lower():
                beds = _parse_int(text)
            elif "bathroom" in svg_classes.lower() or "bath" in svg_classes.lower():
                baths = _parse_int(text)

    if beds is None and len(feature_spans) >= 1:
        non_size = [s for s in feature_spans if "m²" not in s.get_text()]
        if len(non_size) >= 1:
            beds = _parse_int(non_size[0].get_text(strip=True))
        if len(non_size) >= 2 and baths is None:
            baths = _parse_int(non_size[1].get_text(strip=True))

    img = tile.select_one("img.js_P24_listingImage")
    image_url = None
    if img:
        image_url = img.get("src") or img.get("data-src")

    property_type = None
    title_lower = title.lower()

    for ptype in sorted(RESIDENTIAL_PROPERTY_TYPES, key=len, reverse=True):
        if ptype in title_lower:
            property_type = ptype.title()
            break

    return ScrapedListing(
        source="Property24",
        source_url=href,
        source_id=source_id,
        title=title,
        location=location or "Cape Town",
        suburb=suburb,
        price_amount=price_amount,
        price_display=price_display,
        bedrooms=beds,
        bathrooms=baths,
        size_sqm=size,
        property_type=property_type,
        description=None,
        image_url=image_url,
        image_urls=[image_url] if image_url else [],
        contact_name=None,
        contact_phone=None,
    )


def scrape_listing_detail(url: str, client: httpx.Client | None = None) -> dict:
    """Fetch additional detail from an individual listing page."""
    logger.info(f"Scraping listing detail: {url}")

    own_client = client is None
    if own_client:
        client = _get_session()

    try:
        resp = client.get(url)
        resp.raise_for_status()
    finally:
        if own_client:
            client.close()

    soup = BeautifulSoup(resp.text, "html.parser")
    detail: dict = {}

    desc_el = soup.select_one(".js_readMore")
    if desc_el:
        detail["description"] = desc_el.get_text(strip=True)[:2000]

    amenities = []
    for feat in soup.select(".p24_listingFeatures"):
        text = feat.get_text(strip=True)
        if text and ":" not in text:
            amenities.append(text)
    detail["amenities"] = amenities

    features_text = " ".join(
        f.get_text(strip=True).lower() for f in soup.select(".p24_listingFeatures")
    )

    if "furnished" in features_text:
        detail["furnished"] = True
    if "pet friendly" in features_text or "pet" in features_text:
        detail["pets_allowed"] = True

    for row in soup.select(".p24_propertyOverviewRow"):
        key_el = row.select_one(".p24_propertyOverviewKey")
        val_el = row.select_one(".p24_propertyOverviewResult")
        if key_el and val_el:
            key = key_el.get_text(strip=True).lower()
            val = val_el.get_text(strip=True)
            if "floor size" in key:
                size = _parse_int(val)
                if size:
                    detail["size_sqm"] = size
            elif "occupation" in key or "available" in key:
                detail["available_from"] = val

    images = []
    for img in soup.select("img[src*='images.prop24'], img.js_P24_listingImage"):
        src = img.get("src") or img.get("data-src")
        if src and src not in images:
            images.append(src)

    if images:
        detail["image_urls"] = images[:10]
        detail["image_url"] = images[0]

    agent_el = soup.select_one(".p24_agentName, .p24_agent_name")
    if agent_el:
        detail["contact_name"] = agent_el.get_text(strip=True)

    phone_el = soup.select_one(".p24_agentPhone, a[href^='tel:']")
    if phone_el:
        detail["contact_phone"] = phone_el.get_text(strip=True)

    return detail


def run_full_scrape(
    max_pages: int = 3,
    detail_delay: float = 1.0,
    target_suburbs: list[str] | None = None,
) -> list[ScrapedListing]:
    """Run a targeted scrape across selected suburbs."""
    all_listings: list[ScrapedListing] = []
    seen_urls: set[str] = set()

    suburbs_to_scrape = target_suburbs or list(TARGET_SUBURB_URLS.keys())

    for suburb in suburbs_to_scrape:
        search_url = TARGET_SUBURB_URLS.get(suburb)

        if not search_url:
            logger.warning(f"Skipping unknown target suburb: {suburb}")
            continue

        logger.info(f"Starting targeted scrape for {suburb}: {search_url}")

        for page in range(1, max_pages + 1):
            try:
                page_listings = scrape_search_page(
                    page=page,
                    search_url=search_url,
                    expected_suburb=suburb,
                )

                if not page_listings:
                    logger.info(
                        f"No listings found for {suburb} page {page}; moving on"
                    )
                    break

                for listing in page_listings:
                    if listing.source_url not in seen_urls:
                        seen_urls.add(listing.source_url)
                        all_listings.append(listing)

                if page < max_pages:
                    time.sleep(2)

            except Exception:
                logger.exception(f"Failed to scrape {suburb} page {page}")
                continue

        time.sleep(2)

    logger.info(
        f"Targeted scrape complete: {len(all_listings)} unique residential listings "
        f"across {len(suburbs_to_scrape)} target suburbs"
    )

    return all_listings