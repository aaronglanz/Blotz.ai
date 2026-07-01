import json
import re

import httpx


def _parse_json(raw: str) -> dict:
    """Extract JSON from a response that may be wrapped in markdown fences."""
    s = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    s = re.sub(r"```\s*", "", s).strip()
    a = s.find("{")
    b = s.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("No JSON object found in response")
    return json.loads(s[a : b + 1])


def _build_intent_prompt(query: str, location: dict | None) -> str:
    loc_line = ""
    if location:
        loc_line = f"\nLOCATION: {location['name']}, {location['address']}"
    return (
        f'You are a senior Cape Town property expert.\n'
        f'USER INPUT: "{query}"\n'
        f'{loc_line}\n'
        f'Extract: location, type/size, must-haves, lifestyle, environment, building, views, budget. '
        f'Up to 4 missing criteria. Rewrite into improved first-person description under 120 words. '
        f'One-sentence ranking guidance.\n'
        f'JSON only: {{"interpreted_tags":[{{"label":"string","category":"location|lifestyle|must|vibe|budget"}}],'
        f'"missing":[{{"icon":"💰","label":"string","detail":"string"}}],'
        f'"improved_prompt":"string","rank_guidance":"string"}}'
    )


def _build_search_prompt(intent: dict, query: str, location: dict | None) -> str:
    loc_line = ""
    if location:
        loc_line = f"\nTARGET LOCATION: {location['name']} ({location['address']})"
    return (
        f'You are a Cape Town rental property expert with live web search.\n'
        f'BRIEF: "{intent.get("improved_prompt", query)}" | '
        f'Ranking: "{intent.get("rank_guidance", "Match closely.")}"\n'
        f'{loc_line}\n\n'
        f'Search for 8-10 live Cape Town rentals across MULTIPLE sources:\n'
        f'  1. property24.com/to-rent — primary source\n'
        f'  2. privateproperty.co.za/to-rent — secondary source\n'
        f'  3. remax.co.za — additional source\n'
        f'  4. seeff.com — additional source\n'
        f'  5. rawson.co.za — additional source\n'
        f'Search each source and combine the best results. Aim for variety across sources.\n\n'
        f'CRITICAL URL RULE: The url field MUST be the direct individual listing page URL '
        f'(e.g. https://www.property24.com/to-rent/sea-point/cape-town/western-cape/123456 '
        f'or https://www.privateproperty.co.za/to-rent/western-cape/cape-town/...) '
        f'— NOT a search results page. If you cannot find a direct listing URL, omit that result entirely.\n\n'
        f'For each listing: title, location, price, beds, baths, size, furnished, pets, lease, '
        f'amenities, url (direct listing page only), source (site name like "Property24", "Private Property", "RE/MAX", "Seeff", "Rawson").\n'
        f'Try to extract image_url from the listing og:image. If not found return null.\n'
        f'matched[] up to 3 criteria the listing satisfies from the brief, '
        f'not_matched[] up to 2 criteria it does not satisfy. Score 0–100. One sentence match_reason. '
        f'availability "now" or "rare".\n\n'
        f'JSON only: {{"sources_searched":["Property24","Private Property","RE/MAX","Seeff","Rawson"],"results":[{{"title":"","location":"","price":"",'
        f'"beds":2,"baths":1,"size":"","furnished":true,"pets":false,"lease":"","amenities":[],'
        f'"match_score":91,"matched":["Sea views"],"not_matched":["Gym"],"match_reason":"",'
        f'"url":"https://www.property24.com/to-rent/sea-point/cape-town/western-cape/123456",'
        f'"source":"Property24","image_url":null,"availability":"now"}}]}}'
    )


class ClaudeService:
    API_URL = "https://api.anthropic.com/v1/messages"
    INTENT_MODEL = "claude-haiku-4-5-20251001"
    SEARCH_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _extract_text(self, data: dict) -> str:
        """Extract text blocks from Claude response, filtering out tool use/result blocks."""
        blocks = data.get("content", [])
        text = "".join(b["text"] for b in blocks if b.get("type") == "text")
        if not text:
            raise ValueError("No text in Claude response")
        return text

    def interpret_intent_sync(self, query: str, location: dict | None = None) -> dict:
        """Stage 1: Intent interpretation using Claude Haiku."""
        prompt = _build_intent_prompt(query, location)
        body = {
            "model": self.INTENT_MODEL,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(self.API_URL, json=body, headers=self._headers())
            resp.raise_for_status()
        return _parse_json(self._extract_text(resp.json()))

    def search_listings_sync(self, intent: dict, query: str, location: dict | None = None) -> dict:
        """Stage 2: Listing search using Claude Sonnet with web search."""
        prompt = _build_search_prompt(intent, query, location)
        body = {
            "model": self.SEARCH_MODEL,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(self.API_URL, json=body, headers=self._headers())
            resp.raise_for_status()
        return _parse_json(self._extract_text(resp.json()))

    async def interpret_intent(self, query: str, location: dict | None = None) -> dict:
        """Async version of intent interpretation."""
        prompt = _build_intent_prompt(query, location)
        body = {
            "model": self.INTENT_MODEL,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.API_URL, json=body, headers=self._headers())
            resp.raise_for_status()
        return _parse_json(self._extract_text(resp.json()))

    async def search_listings(self, intent: dict, query: str, location: dict | None = None) -> dict:
        """Async version of listing search."""
        prompt = _build_search_prompt(intent, query, location)
        body = {
            "model": self.SEARCH_MODEL,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self.API_URL, json=body, headers=self._headers())
            resp.raise_for_status()
        return _parse_json(self._extract_text(resp.json()))
