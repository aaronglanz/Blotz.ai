import { useEffect, useState } from "react";
import { getNearby } from "../api/locations";
import type { LocationInput, NearbyPlace } from "../types";

const CAT_CLASS: Record<string, string> = {
  food: "nb-ico-food",
  school: "nb-ico-school",
  park: "nb-ico-park",
  shop: "nb-ico-shop",
  transit: "nb-ico-transit",
};

interface Props {
  location: LocationInput | null;
}

export default function LocationContext({ location }: Props) {
  const [nearby, setNearby] = useState<NearbyPlace[]>([]);

  useEffect(() => {
    if (!location?.lat || !location?.lng) {
      setNearby([]);
      return;
    }
    getNearby(location.place_id || "demo", location.lat, location.lng)
      .then(setNearby)
      .catch(() => setNearby([]));
  }, [location]);

  if (!location) return null;

  return (
    <div className="loc-ctx on">
      <div className="lc-top">
        <div className="lc-name">{location.name}</div>
        <div className="lc-badge">Located</div>
      </div>
      <div className="lc-meta">
        <span className="lc-tag">🔑 Rental market active</span>
      </div>
      <div className="lc-addr">📍 {location.address}</div>

      {nearby.length > 0 && (
        <>
          <div style={{ fontSize: 11, color: "var(--ri3)", marginTop: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase" as const }}>
            Nearby
          </div>
          <div className="nearby-grid">
            {nearby.map((n, i) => (
              <div key={i} className="nb-card">
                <div className={`nb-ico ${CAT_CLASS[n.category] || ""}`}>{n.icon}</div>
                <div className="nb-txt">
                  <strong>{n.name}</strong>
                  <span>{n.distance}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
