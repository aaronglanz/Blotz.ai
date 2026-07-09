"""Celery tasks for scraping and caching property listings."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import CachedListing
from app.services.feature_extractor import extract_features
from app.services.scraper import run_full_scrape, scrape_listing_detail, _get_session
from app.tasks import celery_app

logger = logging.getLogger(__name__)

_sync_url = get_settings().DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
_engine = create_engine(_sync_url)
_SessionLocal = sessionmaker(bind=_engine)


def _upsert_listings(db: Session, scraped: list) -> tuple[int, int]:
    """Upsert scraped listings into cached_listings table.

    Returns (inserted, updated) counts.
    """
    now = datetime.now(timezone.utc)
    inserted = 0
    updated = 0

    for item in scraped:
        existing = db.query(CachedListing).filter(
            CachedListing.source_url == item.source_url
        ).first()

        if existing:
            # Update fields that may have changed
            existing.title = item.title
            existing.price_amount = item.price_amount
            existing.price_display = item.price_display
            existing.bedrooms = item.bedrooms
            existing.bathrooms = item.bathrooms
            existing.size_sqm = item.size_sqm
            existing.image_url = item.image_url or existing.image_url
            existing.last_seen_at = now
            existing.is_active = True
            updated += 1
        else:
            listing = CachedListing(
                id=uuid.uuid4(),
                source=item.source,
                source_url=item.source_url,
                source_id=item.source_id,
                title=item.title,
                location=item.location,
                suburb=item.suburb,
                city="Cape Town",
                price_amount=item.price_amount,
                price_display=item.price_display,
                bedrooms=item.bedrooms,
                bathrooms=item.bathrooms,
                size_sqm=item.size_sqm,
                property_type=item.property_type,
                description=item.description,
                amenities=[],
                image_url=item.image_url,
                image_urls=item.image_urls,
                contact_name=item.contact_name,
                contact_phone=item.contact_phone,
                is_active=True,
                first_seen_at=now,
                last_seen_at=now,
                updated_at=now,
            )
            db.add(listing)
            inserted += 1

    db.commit()
    return inserted, updated


@celery_app.task(bind=True, name="scrape.run_property24")
def run_property24_scrape(
    self,
    max_pages: int = 3,
    target_suburbs: list[str] | None = None,
):
    """Scrape targeted Property24 Cape Town residential rentals and cache in DB."""
    logger.info(
        f"Starting targeted Property24 scrape task "
        f"(max_pages={max_pages}, target_suburbs={target_suburbs})"
    )

    db = _SessionLocal()

    try:
        scraped = run_full_scrape(
            max_pages=max_pages,
            target_suburbs=target_suburbs,
        )

        inserted, updated = _upsert_listings(db, scraped)

        # Mark listings not seen recently as potentially inactive.
        # This is intentionally conservative because targeted suburb scraping
        # may not cover every suburb on every run.
        db.execute(
            text("""
                UPDATE cached_listings
                SET is_active = false
                WHERE source = 'Property24'
                  AND last_seen_at < NOW() - INTERVAL '7 days'
                  AND is_active = true
            """)
        )
        db.commit()

        logger.info(
            f"Targeted Property24 scrape complete: "
            f"{inserted} new, {updated} updated, {len(scraped)} total"
        )

        return {
            "inserted": inserted,
            "updated": updated,
            "total": len(scraped),
            "target_suburbs": target_suburbs,
            "max_pages": max_pages,
        }

    except Exception:
        logger.exception("Targeted Property24 scrape failed")
        raise

    finally:
        db.close()

@celery_app.task(bind=True, name="scrape.enrich_listings")
def enrich_listings(self, batch_size: int = 50, delay: float = 3.0):
    """Fetch descriptions and amenities for listings that don't have them yet.

    Uses a persistent HTTP session (reuses cookies) and polite delays
    to avoid rate limiting on Property24 detail pages.
    """
    import time

    logger.info(f"Starting listing enrichment (batch_size={batch_size}, delay={delay}s)")
    db = _SessionLocal()

    try:
        listings = (
            db.query(CachedListing)
            .filter(
                CachedListing.is_active == True,
                CachedListing.description.is_(None),
            )
            .limit(batch_size)
            .all()
        )

        if not listings:
            logger.info("No listings to enrich")
            return {"enriched": 0, "failed": 0}

        logger.info(f"Enriching {len(listings)} listings")
        enriched = 0
        failed = 0
        consecutive_fails = 0

        # Use a persistent session for all detail requests
        session = _get_session()

        try:
            for listing in listings:
                # Back off if we're getting blocked
                if consecutive_fails >= 5:
                    logger.warning("Too many consecutive failures, backing off 30s")
                    time.sleep(30)
                    consecutive_fails = 0
                    # Refresh session
                    session.close()
                    session = _get_session()

                try:
                    url = listing.source_url.split("?")[0]
                    detail = scrape_listing_detail(url, client=session)

                    if detail.get("description"):
                        listing.description = detail["description"]
                    if detail.get("amenities"):
                        listing.amenities = detail["amenities"]
                    if detail.get("furnished") is not None:
                        listing.furnished = detail["furnished"]
                    if detail.get("pets_allowed") is not None:
                        listing.pets_allowed = detail["pets_allowed"]
                    if detail.get("size_sqm") and not listing.size_sqm:
                        listing.size_sqm = detail["size_sqm"]
                    if detail.get("available_from"):
                        listing.available_from = detail["available_from"]
                    if detail.get("image_urls"):
                        listing.image_urls = detail["image_urls"]
                        if not listing.image_url:
                            listing.image_url = detail["image_url"]
                    if detail.get("contact_name"):
                        listing.contact_name = detail["contact_name"]
                    if detail.get("contact_phone"):
                        listing.contact_phone = detail["contact_phone"]

                    # Extract structured feature tags from description
                    features = extract_features(listing.description, listing.amenities)
                    if features:
                        # Merge scraped amenities with extracted features
                        all_amenities = list(set((listing.amenities or []) + features))
                        listing.amenities = all_amenities

                    enriched += 1
                    consecutive_fails = 0
                    db.commit()

                except Exception:
                    logger.debug(f"Failed to enrich listing {listing.id}", exc_info=True)
                    failed += 1
                    consecutive_fails += 1

                time.sleep(delay)
        finally:
            session.close()

        logger.info(f"Enrichment complete: {enriched} enriched, {failed} failed")
        return {"enriched": enriched, "failed": failed}

    except Exception:
        logger.exception("Enrichment task failed")
        raise
    finally:
        db.close()
