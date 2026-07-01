import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import applications, auth, cached_listings, conversations, listings, locations, property_listings, renter, search
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Nestly API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(auth.router)
app.include_router(cached_listings.router)
app.include_router(listings.router)
app.include_router(locations.router)
app.include_router(property_listings.router)
app.include_router(renter.router)
app.include_router(applications.router)
app.include_router(conversations.router)


uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "listings")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/api/uploads/listings", StaticFiles(directory=uploads_dir), name="listing-images")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
