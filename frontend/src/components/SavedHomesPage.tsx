import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createApplication, checkEligible } from "../api/applications";
import { ensureConversation } from "../api/conversations";
import { useSavedListings } from "../hooks/useSavedListings";
import Navbar from "./Navbar";
import ReadinessChecklist from "./ReadinessChecklist";

export default function SavedHomesPage() {
  const navigate = useNavigate();
  const saved = useSavedListings();
  const eligibilityQ = useQuery({
    queryKey: ["eligibility"],
    queryFn: checkEligible,
  });
  const ensureConversationMutation = useMutation({
    mutationFn: ensureConversation,
    onSuccess: (conversation) => navigate(`/inbox?conversation=${conversation.id}`),
  });
  const applyMutation = useMutation({
    mutationFn: createApplication,
    onSuccess: () => navigate("/my-applications"),
  });

  async function handleApply(listingId: string | null) {
    if (!listingId) return;
    if (!eligibilityQ.data?.eligible) {
      navigate("/profile?msg=complete&return=%2Fsaved");
      return;
    }
    applyMutation.mutate(listingId);
  }

  function handleMessage(listingId: string | null) {
    if (!listingId) return;
    ensureConversationMutation.mutate(listingId);
  }

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Your saved homes</h1>
          <p className="lp-sub">
            Keep a shortlist of the properties worth revisiting, compare your next steps,
            and move straight into messaging or applying.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <ReadinessChecklist eligibility={eligibilityQ.data} />

        {saved.isLoading && <div className="sp-loading"><div className="sp-loading-dot" /><p>Loading your shortlist...</p></div>}

        {!saved.isLoading && saved.savedListings.length === 0 && (
          <div className="sp-empty">
            <div className="sp-empty-ico">♡</div>
            <h3>No saved homes yet</h3>
            <p>Save homes from search so you can compare them later without losing your place.</p>
            <Link to="/" className="sp-empty-cta">Browse properties</Link>
          </div>
        )}

        <div className="saved-grid">
          {saved.savedListings.map((listing) => (
            <article key={listing.id} className="saved-card">
              {listing.image_url && (
                <div className="saved-card-image">
                  <img src={listing.image_url} alt={listing.title} />
                </div>
              )}
              <div className="saved-card-body">
                <div className="saved-card-top">
                  <div>
                    <h3>{listing.title}</h3>
                    <p>{listing.location || "Cape Town"} · {listing.price || "Price on request"}</p>
                  </div>
                  <button className="pf-doc-btn pf-doc-remove" onClick={() => saved.toggleSaved(listing)}>
                    Remove
                  </button>
                </div>

                <div className="saved-meta-row">
                  <span>Saved {new Date(listing.saved_at).toLocaleDateString()}</span>
                  <span>{listing.source || "Nestly shortlist"}</span>
                </div>

                <div className="saved-actions">
                  {listing.listing_id ? (
                    <>
                      <button className="sbtn" onClick={() => handleApply(listing.listing_id)} disabled={applyMutation.isPending}>
                        <span className="slbl">Apply now</span>
                      </button>
                      <button className="pf-doc-btn" onClick={() => handleMessage(listing.listing_id)} disabled={ensureConversationMutation.isPending}>
                        Message agent
                      </button>
                    </>
                  ) : (
                    <a className="pf-doc-btn" href={listing.url || undefined} target="_blank" rel="noopener noreferrer">
                      Open listing
                    </a>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
