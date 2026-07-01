import type { LocationInput, Search, SearchResult } from "../types";
import ListingCard from "./ListingCard";
import LocationContext from "./LocationContext";
import ProgressIndicator from "./ProgressIndicator";

interface Props {
  search: Search | null;
  isSearching: boolean;
  savedUrls: Set<string>;
  onToggleSave: (result: SearchResult) => void;
  fallbackImg: (location: string | null) => string;
  selectedLocation: LocationInput | null;
  error: string | null;
}

export default function ResultsSection({
  search,
  isSearching,
  savedUrls,
  onToggleSave,
  fallbackImg,
  selectedLocation,
  error,
}: Props) {
  const results = search?.results
    ? [...search.results].sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0))
    : [];
  const showResults = search?.status === "complete" && results.length > 0;
  const showNoResults = search?.status === "complete" && results.length === 0 && !error;
  const showEmpty = !isSearching && !showResults && !showNoResults && !error;

  return (
    <div className="rs">
      <div className="rsi">
        <LocationContext location={selectedLocation} />

        {isSearching && search && (
          <ProgressIndicator status={search.status} />
        )}

        {error && (
          <div className="errbox on">{error}</div>
        )}

        {isSearching && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="sk on" />
            <div className="sk on" />
            <div className="sk on" />
          </div>
        )}

        {showResults && (
          <>
            <div className="rh on">
              <div className="rh-t">
                Found <b>{results.length}</b> rentals
              </div>
              <div className="rh-m">Ranked by lifestyle match</div>
            </div>

            <div className="grid">
              {results.map((r, i) => (
                <ListingCard
                  key={r.id}
                  result={r}
                  index={i}
                  isSaved={savedUrls.has(r.url || "")}
                  onToggleSave={onToggleSave}
                  fallbackImg={fallbackImg}
                />
              ))}
            </div>
          </>
        )}

        {showNoResults && (
          <div className="empty on">
            <div className="eico">🔍</div>
            <h3>No matches found</h3>
            <p>
              We couldn't find listings matching your criteria.
              <br />
              Try broadening your budget, changing the area, or removing some filters.
            </p>
          </div>
        )}

        {showEmpty && (
          <div className="empty on">
            <div className="eico">🌅</div>
            <h3>Your Cape Town rental is out there</h3>
            <p>
              Use the chat bar above to describe your ideal life.
              <br />
              Search a location, then hit Find.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
