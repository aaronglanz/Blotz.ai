import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Search, SearchResult
from app.services.claude import ClaudeService
from app.tasks import celery_app

logger = logging.getLogger(__name__)

# Sync engine for Celery worker (Celery tasks are synchronous)
_sync_url = get_settings().DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
_engine = create_engine(_sync_url)
_SessionLocal = sessionmaker(bind=_engine)


def _get_db() -> Session:
    return _SessionLocal()


@celery_app.task(bind=True, name="search.run")
def run_search(self, search_id: str):
    settings = get_settings()
    claude = ClaudeService(settings.ANTHROPIC_API_KEY)
    db = _get_db()

    try:
        search = db.query(Search).filter(Search.id == uuid.UUID(search_id)).first()
        if not search:
            logger.error(f"Search {search_id} not found")
            return

        location = None
        if search.interpreted_intent and "location" in search.interpreted_intent:
            location = search.interpreted_intent["location"]

        # Stage 1: Interpret intent
        search.status = "interpreting"
        db.commit()

        try:
            intent = claude.interpret_intent_sync(search.query_text, location)
        except Exception:
            logger.warning("Intent interpretation failed, using fallback")
            intent = {
                "improved_prompt": search.query_text,
                "rank_guidance": "Match closely.",
                "interpreted_tags": [],
                "missing": [],
            }

        search.interpreted_intent = {
            **(search.interpreted_intent or {}),
            "intent": intent,
        }
        db.commit()

        # Stage 2: Search listings
        search.status = "searching"
        db.commit()

        data = claude.search_listings_sync(intent, search.query_text, location)
        results = data.get("results", [])
        results.sort(key=lambda r: r.get("match_score", 0), reverse=True)

        for i, r in enumerate(results):
            result = SearchResult(
                id=uuid.uuid4(),
                search_id=search.id,
                title=r.get("title", "Rental"),
                location=r.get("location"),
                price=r.get("price"),
                beds=r.get("beds"),
                baths=r.get("baths"),
                size=r.get("size"),
                furnished=r.get("furnished"),
                pets=r.get("pets"),
                lease=r.get("lease"),
                amenities=r.get("amenities", []),
                match_score=r.get("match_score"),
                matched=r.get("matched", []),
                not_matched=r.get("not_matched", []),
                match_reason=r.get("match_reason"),
                url=r.get("url"),
                source=r.get("source"),
                image_url=r.get("image_url"),
                availability=r.get("availability"),
                rank=i + 1,
            )
            db.add(result)

        search.status = "complete"
        db.commit()
        logger.info(f"Search {search_id} complete with {len(results)} results")

    except Exception as e:
        logger.exception(f"Search {search_id} failed")
        try:
            search = db.query(Search).filter(Search.id == uuid.UUID(search_id)).first()
            if search:
                search.status = "failed"
                search.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
