import { useNavigate, useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getPropertyListing } from "../api/propertyListings";
import { checkEligible, createApplication } from "../api/applications";
import { ensureConversation } from "../api/conversations";
import { useSavedListings } from "../hooks/useSavedListings";
import Navbar from "./Navbar";

const FALLBACK_IMG = "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=800&q=75";

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const savedListings = useSavedListings();

  const listingQ = useQuery({
    queryKey: ["listing", id],
    queryFn: () => getPropertyListing(id!),
    enabled: !!id,
  });

  const eligibilityQ = useQuery({
    queryKey: ["eligibility"],
    queryFn: checkEligible,
  });

  const applyMutation = useMutation({
    mutationFn: createApplication,
    onSuccess: () => navigate("/my-applications"),
  });

  const messageMutation = useMutation({
    mutationFn: ensureConversation,
    onSuccess: (conversation) => navigate(`/inbox?conversation=${conversation.id}`),
  });

  const listing = listingQ.data;

  function handleApply() {
    if (!listing) return;
    if (!eligibilityQ.data?.eligible) {
      navigate(`/profile?msg=complete&return=/listings/${id}`);
      return;
    }
    applyMutation.mutate(listing.id);
  }

  if (listingQ.isLoading) {
    return (
      <div className="lp-page">
        <Navbar />
        <div className="lp-hero">
          <div className="lp-hero-inner">
            <h1>Loading...</h1>
          </div>
          <div className="lp-hero-fade" />
        </div>
      </div>
    );
  }

  if (listingQ.isError || !listing) {
    return (
      <div className="lp-page">
        <Navbar />
        <div className="lp-hero">
          <div className="lp-hero-inner">
            <h1>Listing not found</h1>
            <p className="lp-sub">This listing may have been removed or the link is incorrect.</p>
          </div>
          <div className="lp-hero-fade" />
        </div>
        <div className="lp-body">
          <Link to="/" className="lp-back-link">Back to search</Link>
        </div>
      </div>
    );
  }

  const imgSrc = listing.image_url || FALLBACK_IMG;
  const isSaved = savedListings.savedListings.some((s) => s.listing_id === listing.id);

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>{listing.title}</h1>
          <p className="lp-sub">{listing.location} &middot; {listing.price}</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body" style={{ maxWidth: 800 }}>
        <Link to="/" className="lp-back-link" style={{ marginBottom: 20, display: "inline-block" }}>
          &larr; Back to search
        </Link>

        {/* Image */}
        <div className="ld-image">
          <img src={imgSrc} alt={listing.title} />
          <button
            className={`save-btn overlay${isSaved ? " saved" : ""}`}
            onClick={() => savedListings.toggleSaved({
              id: listing.id,
              title: listing.title,
              location: listing.location,
              price: listing.price,
              image_url: listing.image_url || null,
              url: null,
              source: "Nestly",
            })}
          >
            {isSaved ? "❤️" : "🤍"}
          </button>
        </div>

        {/* Stats */}
        <section className="lp-section" style={{ marginTop: 20 }}>
          <div className="ld-stats">
            <div className="ld-stat">
              <span className="ld-stat-val">{listing.bedrooms}</span>
              <span className="ld-stat-label">Bedrooms</span>
            </div>
            <div className="ld-stat">
              <span className="ld-stat-val">{listing.bathrooms}</span>
              <span className="ld-stat-label">Bathrooms</span>
            </div>
            {listing.size && (
              <div className="ld-stat">
                <span className="ld-stat-val">{listing.size}</span>
                <span className="ld-stat-label">Size</span>
              </div>
            )}
            <div className="ld-stat">
              <span className="ld-stat-val">{listing.furnished === "yes" ? "Yes" : listing.furnished === "partially" ? "Partial" : "No"}</span>
              <span className="ld-stat-label">Furnished</span>
            </div>
            <div className="ld-stat">
              <span className="ld-stat-val">{listing.pets_allowed ? "Yes" : "No"}</span>
              <span className="ld-stat-label">Pets</span>
            </div>
          </div>
        </section>

        {/* Description */}
        {listing.description && (
          <section className="lp-section" style={{ marginTop: 16 }}>
            <h3 className="lp-sh">About this property</h3>
            <p style={{ fontSize: "13.5px", color: "var(--t2)", lineHeight: 1.7, whiteSpace: "pre-line" }}>
              {listing.description}
            </p>
          </section>
        )}

        {/* Amenities */}
        {listing.amenities.length > 0 && (
          <section className="lp-section" style={{ marginTop: 16 }}>
            <h3 className="lp-sh">Amenities</h3>
            <div className="sp-card-tags" style={{ marginTop: 12 }}>
              {listing.amenities.map((a) => (
                <span key={a} className="sp-tag">{a}</span>
              ))}
            </div>
          </section>
        )}

        {/* Details */}
        <section className="lp-section" style={{ marginTop: 16 }}>
          <h3 className="lp-sh">Details</h3>
          <div className="ld-details">
            {listing.lease_type && (
              <div className="ld-detail-item">
                <span className="ld-detail-label">Lease</span>
                <span>{listing.lease_type}</span>
              </div>
            )}
            {listing.available_from && (
              <div className="ld-detail-item">
                <span className="ld-detail-label">Available from</span>
                <span>{listing.available_from}</span>
              </div>
            )}
          </div>
        </section>

        {/* Contact & Actions */}
        <section className="lp-section lp-section-highlight" style={{ marginTop: 16 }}>
          <h3 className="lp-sh">Contact</h3>
          <p style={{ fontSize: "13.5px", color: "var(--t1)", marginBottom: 4 }}>
            {listing.contact_name}
          </p>
          <p style={{ fontSize: "12.5px", color: "var(--t2)", marginBottom: 16 }}>
            {listing.contact_email}
            {listing.contact_phone && <> &middot; {listing.contact_phone}</>}
          </p>

          <div className="sp-card-btns">
            <button
              className="pf-doc-btn"
              onClick={() => messageMutation.mutate(listing.id)}
              disabled={messageMutation.isPending}
            >
              {messageMutation.isPending ? "Opening..." : "Message Agent"}
            </button>
            <button
              className="sbtn"
              onClick={handleApply}
              disabled={applyMutation.isPending}
            >
              <span className="spin" />
              <span className="slbl">
                {applyMutation.isPending ? "Applying..." : eligibilityQ.data?.eligible ? "Instant Apply" : "Complete profile to apply"}
              </span>
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
