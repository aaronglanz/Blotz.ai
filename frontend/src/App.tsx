import { useCallback, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { submitSearch, getSearch, getSearchHistory } from "./api/search";
import { useHexCanvas } from "./hooks/useHexCanvas";
import { useSavedListings } from "./hooks/useSavedListings";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import SearchBar from "./components/SearchBar";
import PreferenceChips from "./components/PreferenceChips";
import TrustBadges from "./components/TrustBadges";
import ResultsSection from "./components/ResultsSection";
import type { LocationInput, Search, SearchResult } from "./types";

const SUBURB_IMGS: Record<string, string> = {
  "sea point": "photo-1580060839134-75a5edca2e99",
  "camps bay": "photo-1596394516093-501ba68a0ba6",
  clifton: "photo-1564013799919-ab600027ffc6",
  "green point": "photo-1512917774080-9991f1c4c750",
  "bantry bay": "photo-1613977257363-707ba9348227",
  "mouille point": "photo-1580587771525-78b9dba3b914",
  "de waterkant": "photo-1493809842364-78817add7ffb",
  oranjezicht: "photo-1568605114967-8130f3a36994",
  fresnaye: "photo-1600585154340-be6161a56a0c",
  "hout bay": "photo-1583847268964-b28dc8f51f92",
  constantia: "photo-1571939228382-b2f2b585ce15",
  woodstock: "photo-1558618666-fcd25c85cd64",
  observatory: "photo-1600566753190-17f0baa2a6c3",
  claremont: "photo-1600047509807-ba8f99d2cdde",
  bloubergstrand: "photo-1580587771525-78b9dba3b914",
  "city bowl": "photo-1580060839134-75a5edca2e99",
  default: "photo-1580060839134-75a5edca2e99",
};

export function fallbackImg(location: string | null): string {
  const key =
    Object.keys(SUBURB_IMGS).find((k) =>
      (location || "").toLowerCase().includes(k),
    ) || "default";
  return `https://images.unsplash.com/${SUBURB_IMGS[key]}?w=600&q=70&auto=format`;
}

export default function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useHexCanvas(canvasRef);

  const [query, setQuery] = useState("");
  const [selectedLocation, setSelectedLocation] = useState<LocationInput | null>(null);
  const [activeChips, setActiveChips] = useState<Set<string>>(new Set());
  const [searchId, setSearchId] = useState<string | null>(null);
  const savedListings = useSavedListings();

  // Search history
  const historyQuery = useQuery({
    queryKey: ["search-history"],
    queryFn: getSearchHistory,
  });

  // Poll active search
  const searchQuery = useQuery({
    queryKey: ["search", searchId],
    queryFn: () => getSearch(searchId!),
    enabled: !!searchId,
    refetchInterval: (query) => {
      const search = query.state.data as Search | undefined;
      if (!search) return 1500;
      return search.status === "complete" || search.status === "failed"
        ? false
        : 1500;
    },
  });

  const search = searchQuery.data;
  const isSearching =
    !!searchId &&
    search?.status !== "complete" &&
    search?.status !== "failed";

  const submitMutation = useMutation({
    mutationFn: submitSearch,
    onSuccess: (data) => {
      setSearchId(data.id);
      historyQuery.refetch();
    },
  });

  const handleSubmit = useCallback(() => {
    const q = query.trim();
    if (!q) return;
    submitMutation.mutate({
      query_text: q,
      location: selectedLocation || undefined,
    });
  }, [query, selectedLocation, submitMutation]);

  const handleQueryChange = useCallback((val: string) => {
    setQuery(val);
  }, []);

  const handleChipToggle = useCallback((text: string, isOn: boolean) => {
    setActiveChips((prev) => {
      const next = new Set(prev);
      if (isOn) next.add(text);
      else next.delete(text);
      return next;
    });
    if (isOn) {
      setQuery((prev) => {
        const cur = prev.trimEnd();
        return cur + (cur ? ", " : "") + text;
      });
    } else {
      setQuery((prev) => {
        const re = new RegExp(`[,.]?\\s*${text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*[,.]?`, "gi");
        return prev.replace(re, " ").replace(/\s{2,}/g, " ").trim();
      });
    }
  }, []);

  const handleSelectRecent = useCallback((q: string) => {
    setQuery(q);
  }, []);

  return (
    <>
      <Navbar variant="dark" />
      <div className="hero">
        <div className="hero-photo" />
        <div className="hero-grade" />
        <canvas ref={canvasRef} id="hexCanvas" />
        <div className="hero-fade" />

        <div className="hi">
          <HeroSection
            recentSearches={historyQuery.data || []}
            onSelectRecent={handleSelectRecent}
          />
          <SearchBar
            query={query}
            onQueryChange={handleQueryChange}
            onSubmit={handleSubmit}
            isLoading={isSearching}
          />
          <PreferenceChips
            activeChips={activeChips}
            onToggle={handleChipToggle}
            onLocationSelect={(name, loc) => {
              setSelectedLocation(loc);
              handleChipToggle("in " + name, true);
            }}
            onLocationDeselect={(name) => {
              setSelectedLocation(null);
              handleChipToggle("in " + name, false);
            }}
            selectedLocation={selectedLocation}
            onLocationChange={setSelectedLocation}
          />
          <div className="cbar-foot">
            <span className="cfhint">
              Describe freely · AI expands your intent &nbsp;·&nbsp;{" "}
              <kbd>{navigator.platform.includes("Mac") ? "\u2318" : "Ctrl"} Enter</kbd>
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <button
                className={`sbtn${isSearching ? " loading" : ""}`}
                onClick={handleSubmit}
                disabled={isSearching}
              >
                <div className="spin" />
                <span className="slbl">Find my rental &rarr;</span>
              </button>
            </div>
          </div>
          <TrustBadges />
        </div>
      </div>

      <ResultsSection
        search={search || null}
        isSearching={isSearching}
        savedUrls={new Set(savedListings.savedListings.map((listing) => listing.url).filter((url): url is string => !!url))}
        onToggleSave={(result: SearchResult) => savedListings.toggleSaved(result)}
        fallbackImg={fallbackImg}
        selectedLocation={selectedLocation}
        error={submitMutation.error?.message || search?.error_message || null}
      />
    </>
  );
}
