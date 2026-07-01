import type { SearchHistoryItem } from "../types";

interface Props {
  recentSearches: SearchHistoryItem[];
  onSelectRecent: (query: string) => void;
}

export default function HeroSection({ recentSearches, onSelectRecent }: Props) {
  return (
    <>
      <h1>
        Howzit! Describe your
        <br />
        ideal rental. We'll find it.
      </h1>
      <p className="hero-sub">
        Get specific — natural light, a balcony, quiet streets, beach walks… we'll find places that match.
      </p>

      {recentSearches.length > 0 && (
        <div className="recent-row">
          <span className="recent-label">Recent:</span>
          {recentSearches.slice(0, 3).map((s) => (
            <span
              key={s.id}
              className="recent-chip"
              onClick={() => onSelectRecent(s.query_text)}
            >
              <span className="rci">🕐</span>
              {s.query_text.slice(0, 40)}
              {s.query_text.length > 40 ? "…" : ""}
            </span>
          ))}
        </div>
      )}
    </>
  );
}
