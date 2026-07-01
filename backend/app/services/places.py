import math

import httpx

DEMO_PLACES = [
    {"main": "Sea Point", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🌊", "lat": -33.9194, "lng": 18.3877},
    {"main": "Camps Bay", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🏖", "lat": -33.9506, "lng": 18.3773},
    {"main": "Green Point", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🟢", "lat": -33.9056, "lng": 18.4088},
    {"main": "Clifton", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🌅", "lat": -33.9375, "lng": 18.3741},
    {"main": "De Waterkant", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🎨", "lat": -33.9192, "lng": 18.4163},
    {"main": "Mouille Point", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "⚓", "lat": -33.9014, "lng": 18.4031},
    {"main": "Oranjezicht", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🍊", "lat": -33.9334, "lng": 18.4168},
    {"main": "Fresnaye", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🌺", "lat": -33.9211, "lng": 18.3873},
    {"main": "Bantry Bay", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🦅", "lat": -33.9274, "lng": 18.3760},
    {"main": "Hout Bay", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🚢", "lat": -34.0393, "lng": 18.3567},
    {"main": "Constantia", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🍷", "lat": -34.0235, "lng": 18.4285},
    {"main": "Woodstock", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🏭", "lat": -33.9327, "lng": 18.4420},
    {"main": "Observatory", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🔭", "lat": -33.9408, "lng": 18.4693},
    {"main": "Claremont", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "🏫", "lat": -33.9862, "lng": 18.4653},
    {"main": "Bloubergstrand", "sec": "Cape Town, Western Cape", "type": "suburb", "icon": "💨", "lat": -33.8116, "lng": 18.4674},
    {"main": "City Bowl", "sec": "Cape Town, Western Cape", "type": "area", "icon": "🏙", "lat": -33.9258, "lng": 18.4232},
]

DEMO_NEARBY: dict[str, list[dict]] = {
    "Sea Point": [
        {"ico": "🏖", "cat": "park", "name": "Sea Point Promenade", "dist": "180m"},
        {"ico": "☕", "cat": "food", "name": "Bootlegger Coffee", "dist": "0.3km"},
        {"ico": "🏋", "cat": "shop", "name": "Virgin Active", "dist": "0.5km"},
        {"ico": "🏥", "cat": "shop", "name": "Netcare Clinic", "dist": "0.8km"},
    ],
    "Camps Bay": [
        {"ico": "🏖", "cat": "park", "name": "Camps Bay Beach", "dist": "50m"},
        {"ico": "🍽", "cat": "food", "name": "The Kove", "dist": "0.2km"},
        {"ico": "🛒", "cat": "shop", "name": "Pick n Pay", "dist": "0.4km"},
        {"ico": "🚌", "cat": "transit", "name": "MyCiTi Bus Stop", "dist": "0.6km"},
    ],
    "default": [
        {"ico": "☕", "cat": "food", "name": "Local Café", "dist": "0.3km"},
        {"ico": "🛒", "cat": "shop", "name": "Supermarket", "dist": "0.5km"},
        {"ico": "🚌", "cat": "transit", "name": "Bus Stop", "dist": "0.4km"},
        {"ico": "🌳", "cat": "park", "name": "Park", "dist": "0.7km"},
    ],
}

NEARBY_TYPES = [
    {"type": "cafe", "ico": "☕", "cat": "food"},
    {"type": "school", "ico": "🏫", "cat": "school"},
    {"type": "park", "ico": "🌳", "cat": "park"},
    {"type": "supermarket", "ico": "🛒", "cat": "shop"},
    {"type": "transit_station", "ico": "🚌", "cat": "transit"},
]


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _format_dist(meters: float) -> str:
    if meters < 1000:
        return f"{int(meters)}m"
    return f"{meters / 1000:.1f}km"


class PlacesService:
    AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    async def autocomplete(self, input_text: str) -> list[dict]:
        if not self.api_key:
            return self._demo_autocomplete(input_text)

        params = {
            "input": input_text,
            "key": self.api_key,
            "location": "-33.92,18.42",
            "radius": "30000",
            "components": "country:za",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.AUTOCOMPLETE_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        predictions = []
        for p in data.get("predictions", []):
            st = p.get("structured_formatting", {})
            predictions.append({
                "place_id": p["place_id"],
                "main_text": st.get("main_text", p.get("description", "")),
                "secondary_text": st.get("secondary_text", ""),
                "description": p.get("description", ""),
            })
        return predictions

    async def get_nearby(self, lat: float, lng: float) -> list[dict]:
        if not self.api_key:
            return self._demo_nearby(lat, lng)

        results = []
        async with httpx.AsyncClient(timeout=10) as client:
            for nt in NEARBY_TYPES:
                params = {
                    "location": f"{lat},{lng}",
                    "radius": "800",
                    "type": nt["type"],
                    "key": self.api_key,
                }
                resp = await client.get(self.NEARBY_URL, params=params)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                places = data.get("results", [])
                if not places:
                    continue
                r = places[0]
                rlat = r["geometry"]["location"]["lat"]
                rlng = r["geometry"]["location"]["lng"]
                dist = _haversine(lat, lng, rlat, rlng)
                results.append({
                    "name": r["name"],
                    "icon": nt["ico"],
                    "category": nt["cat"],
                    "distance": _format_dist(dist),
                })
        return results

    async def get_place_details(self, place_id: str) -> dict | None:
        if not self.api_key:
            return None
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,types",
            "key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(self.DETAILS_URL, params=params)
            resp.raise_for_status()
        result = resp.json().get("result")
        if not result:
            return None
        geo = result.get("geometry", {}).get("location", {})
        return {
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "lat": geo.get("lat"),
            "lng": geo.get("lng"),
            "types": result.get("types", []),
        }

    def _demo_autocomplete(self, input_text: str) -> list[dict]:
        query = input_text.lower()
        results = []
        for p in DEMO_PLACES:
            if query in p["main"].lower():
                results.append({
                    "place_id": f"demo_{p['main'].lower().replace(' ', '_')}",
                    "main_text": p["main"],
                    "secondary_text": p["sec"],
                    "description": f"{p['main']}, {p['sec']}",
                })
        return results[:5]

    def _demo_nearby(self, lat: float, lng: float) -> list[dict]:
        closest = min(DEMO_PLACES, key=lambda p: _haversine(lat, lng, p["lat"], p["lng"]))
        nearby = DEMO_NEARBY.get(closest["main"], DEMO_NEARBY["default"])
        return [{"name": n["name"], "icon": n["ico"], "category": n["cat"], "distance": n["dist"]} for n in nearby]
