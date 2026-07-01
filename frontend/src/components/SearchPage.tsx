import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { searchPropertyListings } from "../api/propertyListings";
import { checkEligible, createApplication } from "../api/applications";
import { ensureConversation } from "../api/conversations";
import { useSavedListings } from "../hooks/useSavedListings";
import Navbar from "./Navbar";
import ReadinessChecklist from "./ReadinessChecklist";
import type { RankedListing } from "../types";

const FILTER_BUBBLES = [
  { label: "Sea views", icon: "🌊" },
  { label: "Mountain views", icon: "⛰️" },
  { label: "Pool", icon: "🏊" },
  { label: "Solar", icon: "☀️" },
  { label: "Pet friendly", icon: "🐾" },
  { label: "3+ beds", icon: "🛏️" },
  { label: "2+ beds", icon: "🛏️" },
  { label: "Under R3m", icon: "💰" },
  { label: "R3m–R6m", icon: "💎" },
  { label: "R6m–R10m", icon: "🏆" },
  { label: "Camps Bay", icon: "📍" },
  { label: "Clifton", icon: "📍" },
  { label: "Bantry Bay", icon: "📍" },
  { label: "Sea Point", icon: "📍" },
  { label: "Green Point", icon: "📍" },
];

const FALLBACK_IMAGES: Record<string, string> = {
  "Sea Point": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=600&q=75",
  "Camps Bay": "https://images.unsplash.com/photo-1591280063444-d3c514eb6e13?w=600&q=75",
  "Green Point": "https://images.unsplash.com/photo-1577948000111-9c970dfe3743?w=600&q=75",
  "Clifton": "https://images.unsplash.com/photo-1591280063444-d3c514eb6e13?w=600&q=75",
  "Bantry Bay": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=600&q=75",
  "Woodstock": "https://images.unsplash.com/photo-1577948000111-9c970dfe3743?w=600&q=75",
  "Gardens": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=600&q=75",
};

function getMatchColor(pct: number) {
  if (pct >= 80) return { bg: "#eaf5ee", color: "#2a6348", border: "#a8d8b8" };
  if (pct >= 50) return { bg: "#fff8e4", color: "#7a5010", border: "#e8c870" };
  return { bg: "#f3f1ee", color: "#8a847c", border: "#d0cbc4" };
}

function getListingImage(listing: RankedListing) {
  return listing.image_url || FALLBACK_IMAGES[listing.location] || FALLBACK_IMAGES["Sea Point"];
}

export default function SearchPage() {
  const navigate = useNavigate();
  const savedListings = useSavedListings();
  const [query, setQuery] = useState("");
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<RankedListing[] | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [applyingTo, setApplyingTo] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState<RankedListing | null>(null);

  const eligibilityQ = useQuery({
    queryKey: ["eligibility"],
    queryFn: checkEligible,
  });

  const mutation = useMutation({
    mutationFn: searchPropertyListings,
    onSuccess: (data) => {
      setResults(data.results);
      setHasSearched(true);
    },
  });

  const applyMutation = useMutation({
    mutationFn: createApplication,
    onSuccess: () => {
      setShowConfirm(null);
      setApplyingTo(null);
      navigate("/my-applications");
    },
    onError: () => {
      setApplyingTo(null);
    },
  });

  const ensureConversationMutation = useMutation({
    mutationFn: ensureConversation,
    onSuccess: (conversation) => navigate(`/inbox?conversation=${conversation.id}`),
  });

  function handleApplyClick(listing: RankedListing) {
    if (!eligibilityQ.data?.eligible) {
      navigate("/profile?msg=complete&return=%2F");
      return;
    }
    setShowConfirm(listing);
  }

  function confirmApply() {
    if (!showConfirm) return;
    setApplyingTo(showConfirm.id);
    applyMutation.mutate(showConfirm.id);
  }

  function toggleFilter(label: string) {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  function handleSearch() {
    const searchQuery = query.trim() || [...activeFilters].join(", ");
    if (!searchQuery) return;
    mutation.mutate({ query: searchQuery, filters: [...activeFilters] });
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  }

  return (
    <div className="sp-page">
      <Navbar />

      <div className="sp-hero">
        <div className="sp-hero-inner">
          <h1>Find your perfect home</h1>
          <p className="sp-hero-sub">
            Tell us what you&apos;re looking for and build a shortlist you can save, message, and apply from.
          </p>

          <div className="sp-searchbar">
            <textarea
              className="sp-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="3-bed with sea views under R8m in Camps Bay..."
              rows={2}
            />
            <button
              className={`sbtn sp-search-btn ${mutation.isPending ? "loading" : ""}`}
              onClick={handleSearch}
              disabled={mutation.isPending}
            >
              <span className="spin" />
              <span className="slbl">{mutation.isPending ? "Searching..." : "Search"}</span>
            </button>
          </div>

          <div className="sp-filters">
            {FILTER_BUBBLES.map((f) => (
              <button
                key={f.label}
                className={`sp-bubble ${activeFilters.has(f.label) ? "on" : ""}`}
                onClick={() => toggleFilter(f.label)}
              >
                <span className="sp-bubble-ico">{f.icon}</span>
                {f.label}
              </button>
            ))}
          </div>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="sp-results">
        <div className="sp-results-inner">
          <ReadinessChecklist eligibility={eligibilityQ.data} />

          {mutation.isPending && (
            <div className="sp-loading">
              <div className="sp-loading-dot" />
              <p>Our AI is matching you with the best properties...</p>
            </div>
          )}

          {mutation.isError && (
            <div className="lp-error" style={{ marginBottom: 20 }}>
              Something went wrong. Please try again.
            </div>
          )}

          {hasSearched && !mutation.isPending && results && results.length === 0 && (
            <div className="sp-empty">
              <div className="sp-empty-ico">🏡</div>
              <h3>No listings yet</h3>
              <p>We&apos;re onboarding agents now. Check back soon.</p>
              <Link to="/list-property" className="sp-empty-cta">Are you an agent? List a property</Link>
            </div>
          )}

          {results && results.length > 0 && !mutation.isPending && (
            <>
              <div className="sp-results-hdr">
                <h2>{results.length} {results.length === 1 ? "property" : "properties"} matched</h2>
                <Link to="/saved" className="sp-inline-link">View saved homes</Link>
              </div>
              <div className="sp-grid">
                {results.map((listing) => {
                  const mc = getMatchColor(listing.match_pct);
                  const imgSrc = getListingImage(listing);
                  const isSaved = savedListings.isSaved(listing);
                  return (
                    <div key={listing.id} className="sp-card">
                      <div className="sp-card-img">
                        <img src={imgSrc} alt={listing.title} />
                        <div
                          className="sp-match-badge"
                          style={{ background: mc.bg, color: mc.color, borderColor: mc.border }}
                        >
                          {listing.match_pct}% match
                        </div>
                        <button
                          className={`save-btn overlay${isSaved ? " saved" : ""}`}
                          onClick={() => savedListings.toggleSaved(listing)}
                        >
                          {isSaved ? "❤️" : "🤍"}
                        </button>
                      </div>

                      <div className="sp-card-body">
                        <div className="sp-card-headline">
                          <div>
                            <h3 className="sp-card-title">{listing.title}</h3>
                            <div className="sp-card-price">{listing.price}</div>
                          </div>
                          {isSaved && <span className="readiness-badge ok">Saved</span>}
                        </div>

                        <div className="sp-card-meta">
                          {listing.location} &middot; {listing.bedrooms} bed{listing.bedrooms !== 1 && "s"} &middot; {listing.bathrooms} bath{listing.bathrooms !== 1 && "s"}
                          {listing.size && <> &middot; {listing.size}</>}
                        </div>

                        {listing.amenities.length > 0 && (
                          <div className="sp-card-tags">
                            {listing.amenities.slice(0, 5).map((amenity) => (
                              <span key={amenity} className="sp-tag">{amenity}</span>
                            ))}
                          </div>
                        )}

                        <p className="sp-card-reason">{listing.match_reason}</p>
                        <ReadinessChecklist eligibility={eligibilityQ.data} compact />

                        <div className="sp-card-footer">
                          <span className="sp-agent">{listing.contact_name}</span>
                          <div className="sp-card-btns">
                            <button
                              className="pf-doc-btn"
                              onClick={() => ensureConversationMutation.mutate(listing.id)}
                              disabled={ensureConversationMutation.isPending}
                            >
                              Message Agent
                            </button>
                            <button
                              className="sbtn sp-apply-btn"
                              onClick={() => handleApplyClick(listing)}
                              disabled={applyingTo === listing.id}
                            >
                              <span className="slbl">
                                {eligibilityQ.data?.eligible ? "Instant Apply ⚡" : "Finish profile"}
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>

      {showConfirm && (
        <div className="modal-overlay" onClick={() => setShowConfirm(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm application</h3>
            <p>
              Send your verified profile to <strong>{showConfirm.contact_name}</strong> for{" "}
              <strong>{showConfirm.title}</strong> in {showConfirm.location}?
            </p>
            <ReadinessChecklist eligibility={eligibilityQ.data} compact />
            <div className="modal-actions">
              <button className="pf-doc-btn" onClick={() => setShowConfirm(null)}>Cancel</button>
              <button className="sbtn" onClick={confirmApply} disabled={applyMutation.isPending}>
                <span className="spin" />
                <span className="slbl">{applyMutation.isPending ? "Sending..." : "Confirm"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
