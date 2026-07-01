"""Property24 scraper for Cape Town rental listings.

Fetches listing data from Property24 search results pages and individual
listing pages, returning normalized dicts ready for upsert into cached_listings.
"""

import logging
import re
import time
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

BASE_URL = "https://www.property24.com"
SEARCH_URL = f"{BASE_URL}/to-rent/cape-town/western-cape/432"

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
    """Extract numeric price (in rands) and display string from price text."""
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
    """Extract the Property24 listing ID from a URL like /to-rent/.../12345678"""
    match = re.search(r"/(\d{6,})", url)
    return match.group(1) if match else None


def _get_client() -> httpx.Client:
    import random
    return httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers={**HEADERS, "User-Agent": random.choice(USER_AGENTS)},
    )


def _get_session() -> httpx.Client:
    """Create a persistent session that mimics a real browser.

    Visits the search page first to collect cookies before hitting detail pages.
    """
    import random
    client = httpx.Client(
        timeout=30,
        follow_redirects=True,
        headers={
            **HEADERS,
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": SEARCH_URL,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        },
    )
    # Warm up with a search page visit to get cookies
    try:
        client.get(SEARCH_URL)
    except Exception:
        pass
    return client


def scrape_search_page(page: int = 1) -> list[ScrapedListing]:
    """Scrape a single page of Property24 Cape Town rental search results."""
    url = SEARCH_URL if page == 1 else f"{SEARCH_URL}/p{page}"
    logger.info(f"Scraping Property24 search page {page}: {url}")

    with _get_client() as client:
        resp = client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    listings: list[ScrapedListing] = []

    # Property24 uses .js_resultTile (underscore) for listing cards
    tiles = soup.select(".js_resultTile")

    for tile in tiles:
        try:
            listing = _parse_tile(tile)
            if listing:
                listings.append(listing)
        except Exception:
            logger.debug("Failed to parse tile", exc_info=True)
            continue

    logger.info(f"Page {page}: found {len(listings)} listings")
    return listings


def _parse_tile(tile: Tag) -> ScrapedListing | None:
    """Parse a single listing tile from search results.

    Tile structure (as of April 2026):
      .js_resultTile
        .p24_proTile (.js_resultTileClickable)
          a[href*='/to-rent/']  — listing link with ID
          img.js_P24_listingImage — main image
          .p24_content
            .p24_price — "R 73 000"
            .p24_description — "2 Bedroom Apartment in"
            .p24_location — "Sea Point"
            .p24_icons
              .p24_featureDetails — beds, baths, garages, size
    """
    # Find the listing link — the anchor with a listing ID in the URL
    link = tile.select_one("a[href*='/to-rent/']")
    if not link or not link.get("href"):
        return None

    href = link["href"]
    if not href.startswith("http"):
        href = BASE_URL + href

    # Must have a listing ID (6+ digits) to be a real listing, not a category page
    source_id = _extract_listing_id(href)
    if not source_id:
        return None

    # Title: combine description + location for a complete title
    desc_el = tile.select_one(".p24_description")
    loc_el = tile.select_one(".p24_location")

    desc_text = desc_el.get_text(strip=True) if desc_el else ""
    location = loc_el.get_text(strip=True) if loc_el else ""

    # The description often ends with "in" or "in<Suburb>" (no space)
    title = desc_text.rstrip()
    # Handle "2 Bedroom Apartment inSea Point" (no space after "in")
    title = re.sub(r"\bin([A-Z])", r"in \1", title)
    # Handle "2 Bedroom Apartment in" (trailing "in" with no suburb)
    if title.endswith(" in") and location:
        title = f"{title} {location}"
    elif location and location not in title:
        title = f"{title} - {location}"

    if not title or len(title) < 5:
        return None

    suburb = location.strip() if location else None

    # Price — .p24_price contains nested children (description, location),
    # so we only want the direct text nodes
    price_el = tile.select_one(".p24_price")
    price_text = ""
    if price_el:
        price_text = "".join(
            child for child in price_el.children if isinstance(child, str)
        ).strip()
    price_amount, price_display = _parse_price(price_text) if price_text else (None, "POA")

    # Features: .p24_featureDetails spans in order: beds, baths, garages, size
    # We identify them by adjacent SVG icons or by position
    feature_spans = tile.select(".p24_featureDetails")
    beds = None
    baths = None
    size = None

    for span in feature_spans:
        text = span.get_text(strip=True)
        # Size has "m²" in it
        if "m²" in text:
            size = _parse_int(text)
            continue

        # Check the preceding sibling SVG for icon type
        prev = span.find_previous_sibling()
        if prev and prev.name == "svg":
            svg_classes = " ".join(prev.get("class", []))
            if "bedroom" in svg_classes.lower() or "bed" in svg_classes.lower():
                beds = _parse_int(text)
            elif "bathroom" in svg_classes.lower() or "bath" in svg_classes.lower():
                baths = _parse_int(text)
            # Skip garage/parking icons

    # If we couldn't identify by icons, use positional order: beds, baths, garages, size
    if beds is None and len(feature_spans) >= 1:
        non_size = [s for s in feature_spans if "m²" not in s.get_text()]
        if len(non_size) >= 1:
            beds = _parse_int(non_size[0].get_text(strip=True))
        if len(non_size) >= 2 and baths is None:
            baths = _parse_int(non_size[1].get_text(strip=True))

    # Image
    img = tile.select_one("img.js_P24_listingImage")
    image_url = None
    if img:
        image_url = img.get("src") or img.get("data-src")

    # Property type from title
    property_type = None
    title_lower = title.lower()
    for ptype in ["apartment", "flat", "house", "townhouse", "penthouse", "cottage", "studio", "duplex"]:
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
    """Fetch additional detail from an individual listing page.

    Returns a dict with description, amenities, images, contact info, and
    structured features like furnished/pets from the detail page.

    Pass an existing `client` session for batch operations (reuses cookies).
    """
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

    # Description
    desc_el = soup.select_one(".js_readMore")
    if desc_el:
        detail["description"] = desc_el.get_text(strip=True)[:2000]

    # Structured features (Pet Friendly, Furnished, Pool, etc.)
    amenities = []
    for feat in soup.select(".p24_listingFeatures"):
        text = feat.get_text(strip=True)
        if text and ":" not in text:
            # Features without values are boolean amenities (e.g. "Pet Friendly", "Pool")
            amenities.append(text)
    detail["amenities"] = amenities

    # Check furnished/pets from features
    features_text = " ".join(f.get_text(strip=True).lower() for f in soup.select(".p24_listingFeatures"))
    if "furnished" in features_text:
        detail["furnished"] = True
    if "pet friendly" in features_text or "pet" in features_text:
        detail["pets_allowed"] = True

    # Property overview rows (floor size, occupation date, etc.)
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

    # All images
    images = []
    for img in soup.select("img[src*='images.prop24'], img.js_P24_listingImage"):
        src = img.get("src") or img.get("data-src")
        if src and src not in images:
            images.append(src)
    if images:
        detail["image_urls"] = images[:10]
        detail["image_url"] = images[0]

    # Agent info
    agent_el = soup.select_one(".p24_agentName, .p24_agent_name")
    if agent_el:
        detail["contact_name"] = agent_el.get_text(strip=True)

    phone_el = soup.select_one(".p24_agentPhone, a[href^='tel:']")
    if phone_el:
        detail["contact_phone"] = phone_el.get_text(strip=True)

    return detail


def run_full_scrape(max_pages: int = 5, detail_delay: float = 1.0) -> list[ScrapedListing]:
    """Run a full scrape across multiple search pages."""
    all_listings: list[ScrapedListing] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        try:
            page_listings = scrape_search_page(page)
            for listing in page_listings:
                if listing.source_url not in seen_urls:
                    seen_urls.add(listing.source_url)
                    all_listings.append(listing)
            if page < max_pages:
                time.sleep(2)
        except Exception:
            logger.exception(f"Failed to scrape page {page}")
            continue

    logger.info(f"Full scrape complete: {len(all_listings)} unique listings across {max_pages} pages")
    return all_listings
