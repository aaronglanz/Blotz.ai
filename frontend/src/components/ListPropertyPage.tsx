import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { createPropertyListing } from "../api/propertyListings";
import AgentPortalLayout from "./AgentPortalLayout";
import type { PropertyListingCreate } from "../types";
import { getAgentAccount, hasAgentAccount } from "../agentPortal";

const AMENITY_OPTIONS = [
  "Parking", "Pool", "Garden", "Gym", "Security", "Balcony",
  "Fibre Internet", "Air Conditioning", "Dishwasher", "Washing Machine",
  "Sea Views", "Mountain Views", "Solar Panels", "Generator", "Rooftop",
];

const CAPE_TOWN_AREAS = [
  "Sea Point", "Camps Bay", "Green Point", "Gardens", "Tamboerskloof",
  "Woodstock", "Observatory", "Claremont", "Newlands", "Rondebosch",
  "Stellenbosch", "Century City", "Bloubergstrand", "Table View",
  "Constantia", "Muizenberg", "Kalk Bay", "Hout Bay", "Clifton", "Bantry Bay",
];

export default function ListPropertyPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<PropertyListingCreate>({
    title: "",
    location: "",
    price: "",
    bedrooms: 1,
    bathrooms: 1,
    size: "",
    furnished: "no",
    pets_allowed: false,
    lease_type: "",
    amenities: [],
    description: "",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    image_url: "",
    available_from: "",
  });
  const agentAccount = getAgentAccount();

  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: createPropertyListing,
    onSuccess: () => setSubmitted(true),
  });

  useEffect(() => {
    if (!hasAgentAccount()) {
      navigate("/agent/signup", { replace: true });
    }
  }, [navigate]);

  function set<K extends keyof PropertyListingCreate>(key: K, val: PropertyListingCreate[K]) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  function toggleAmenity(a: string) {
    setForm((f) => ({
      ...f,
      amenities: f.amenities.includes(a)
        ? f.amenities.filter((x) => x !== a)
        : [...f.amenities, a],
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(form);
  }

  if (submitted) {
    return (
      <AgentPortalLayout requireAuth>
        <div className="lp-body">
          <div className="lp-success">
            <div className="lp-success-ico">&#10003;</div>
            <h2>Your listing is live!</h2>
            <p>
              Renters searching on Nestly can now find your property. Our AI matches it to
              people looking for exactly what you offer — the more detail you gave, the better your matches.
            </p>
            <div className="lp-success-actions">
              <button className="sbtn" onClick={() => { setSubmitted(false); setForm({ title: "", location: "", price: "", bedrooms: 1, bathrooms: 1, size: "", furnished: "no", pets_allowed: false, lease_type: "", amenities: [], description: "", contact_name: "", contact_email: "", contact_phone: "", image_url: "", available_from: "" }); }}>
                <span className="slbl">List another property</span>
              </button>
              <Link to="/agent/applications" className="lp-back-link">Go to agent portal</Link>
            </div>
          </div>
        </div>
      </AgentPortalLayout>
    );
  }

  return (
    <AgentPortalLayout requireAuth>
      {/* Hero with value prop */}
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Publish your first listing</h1>
          <p className="lp-sub">
            This is your first step into the Nestly agent portal. Add your property details below and we&apos;ll turn it into a renter-ready listing.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="lp-callout">
          <div className="lp-callout-item">
            <span className="lp-callout-ico">🪪</span>
            <div>
              <strong>Agent account setup</strong>
              <span>
                Signed in as {agentAccount?.full_name || "Agent"}{agentAccount?.agency_name ? ` · ${agentAccount.agency_name}` : ""}.
              </span>
            </div>
          </div>
        </div>

        {/* Value callout */}
        <div className="lp-callout">
          <div className="lp-callout-item">
            <span className="lp-callout-ico">🎯</span>
            <div>
              <strong>AI-matched leads</strong>
              <span>Buyers describe what they want in natural language — our AI connects them to your listing.</span>
            </div>
          </div>
          <div className="lp-callout-item">
            <span className="lp-callout-ico">✍️</span>
            <div>
              <strong>Description matters</strong>
              <span>A rich description helps AI understand your property's personality and match it to the right people.</span>
            </div>
          </div>
          <div className="lp-callout-item">
            <span className="lp-callout-ico">⚡</span>
            <div>
              <strong>Instant visibility</strong>
              <span>Your listing goes live immediately and appears in search results within seconds.</span>
            </div>
          </div>
        </div>

        <form className="lp-form" onSubmit={handleSubmit}>
          {/* Property Details */}
          <section className="lp-section">
            <h3 className="lp-sh">The basics</h3>
            <p className="lp-sh-hint">Start with the essentials — location, price, and size.</p>
            <label className="lp-label">
              Headline
              <input className="lp-input" required value={form.title} onChange={(e) => set("title", e.target.value)} placeholder="e.g. Bright 2-bed apartment with ocean views in Sea Point" />
              <span className="lp-hint">Make it descriptive — this is the first thing renters see.</span>
            </label>
            <label className="lp-label">
              Area
              <select className="lp-input" required value={form.location} onChange={(e) => set("location", e.target.value)}>
                <option value="">Select area...</option>
                {CAPE_TOWN_AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </label>
            <div className="lp-row">
              <label className="lp-label">
                Monthly rent
                <input className="lp-input" required value={form.price} onChange={(e) => set("price", e.target.value)} placeholder="e.g. R18,500" />
              </label>
              <label className="lp-label">
                Floor size
                <input className="lp-input" value={form.size || ""} onChange={(e) => set("size", e.target.value)} placeholder="e.g. 85m²" />
              </label>
            </div>
            <div className="lp-row">
              <label className="lp-label">
                Bedrooms
                <select className="lp-input" value={form.bedrooms} onChange={(e) => set("bedrooms", +e.target.value)}>
                  {[0, 1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n === 0 ? "Studio" : n}</option>)}
                </select>
              </label>
              <label className="lp-label">
                Bathrooms
                <select className="lp-input" value={form.bathrooms} onChange={(e) => set("bathrooms", +e.target.value)}>
                  {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </label>
            </div>
          </section>

          {/* Features */}
          <section className="lp-section">
            <h3 className="lp-sh">What makes it special</h3>
            <p className="lp-sh-hint">These details help our AI match your property with the right people.</p>
            <div className="lp-field">
              <span className="lp-field-label">Furnished</span>
              <div className="lp-radios">
                {(["no", "yes", "partially"] as const).map((v) => (
                  <label key={v} className={`lp-radio ${form.furnished === v ? "on" : ""}`}>
                    <input type="radio" name="furnished" value={v} checked={form.furnished === v} onChange={() => set("furnished", v)} />
                    {v === "no" ? "Unfurnished" : v === "yes" ? "Fully furnished" : "Partially"}
                  </label>
                ))}
              </div>
            </div>
            <div className="lp-field">
              <span className="lp-field-label">Pets welcome?</span>
              <div className="lp-radios">
                <label className={`lp-radio ${form.pets_allowed ? "on" : ""}`}>
                  <input type="radio" name="pets" checked={form.pets_allowed} onChange={() => set("pets_allowed", true)} /> Yes
                </label>
                <label className={`lp-radio ${!form.pets_allowed ? "on" : ""}`}>
                  <input type="radio" name="pets" checked={!form.pets_allowed} onChange={() => set("pets_allowed", false)} /> No
                </label>
              </div>
            </div>
            <div className="lp-row">
              <label className="lp-label">
                Lease type
                <input className="lp-input" value={form.lease_type || ""} onChange={(e) => set("lease_type", e.target.value)} placeholder="e.g. 12-month, month-to-month" />
              </label>
              <label className="lp-label">
                Available from
                <input className="lp-input" type="date" value={form.available_from || ""} onChange={(e) => set("available_from", e.target.value)} />
              </label>
            </div>
            <div className="lp-field">
              <span className="lp-field-label">Amenities &amp; lifestyle tags</span>
              <span className="lp-hint" style={{ marginBottom: 10, display: "block" }}>Select everything that applies — renters search by these.</span>
              <div className="lp-amenities">
                {AMENITY_OPTIONS.map((a) => (
                  <button type="button" key={a} className={`chip cn ${form.amenities.includes(a) ? "on" : ""}`} onClick={() => toggleAmenity(a)}>
                    {a} {form.amenities.includes(a) && <span className="cx">&#10005;</span>}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Description — emphasised */}
          <section className="lp-section lp-section-highlight">
            <h3 className="lp-sh">Tell the story of this property</h3>
            <p className="lp-sh-hint">
              This is your chance to sell the lifestyle, not just the specs. Think about what it
              <em> feels </em> like to live here. Morning light? Walking distance to the promenade?
              Quiet street? Our AI reads this to match you with buyers who care about exactly these things.
            </p>
            <label className="lp-label">
              <textarea
                className="lp-textarea"
                rows={7}
                value={form.description || ""}
                onChange={(e) => set("description", e.target.value)}
                placeholder={"Wake up to the sound of the ocean in this sun-drenched apartment on the Sea Point promenade. Floor-to-ceiling windows frame Lion's Head, and the open-plan living area flows onto a generous balcony perfect for sundowners. Two minutes' walk to cafes, gyms, and the Saturday market..."}
              />
              <span className="lp-hint">
                Tip: Describe the views, the neighbourhood feel, the morning routine. The more vivid, the better your matches.
              </span>
            </label>
          </section>

          {/* Contact */}
          <section className="lp-section">
            <h3 className="lp-sh">Your contact details</h3>
            <p className="lp-sh-hint">Interested renters will reach out via WhatsApp or email.</p>
            <label className="lp-label">
              Your name
              <input className="lp-input" required value={form.contact_name} onChange={(e) => set("contact_name", e.target.value)} placeholder="Full name" />
            </label>
            <div className="lp-row">
              <label className="lp-label">
                Email
                <input className="lp-input" type="email" required value={form.contact_email} onChange={(e) => set("contact_email", e.target.value)} placeholder="you@example.com" />
              </label>
              <label className="lp-label">
                WhatsApp number
                <input className="lp-input" type="tel" value={form.contact_phone || ""} onChange={(e) => set("contact_phone", e.target.value)} placeholder="+27 82 123 4567" />
                <span className="lp-hint">Renters can message you directly from their search results.</span>
              </label>
            </div>
          </section>

          {/* Media */}
          <section className="lp-section">
            <h3 className="lp-sh">Photos</h3>
            <p className="lp-sh-hint">Upload a photo or paste a URL. A great photo is worth a thousand words.</p>

            {form.image_url && (
              <div className="ld-image" style={{ marginBottom: 14, borderRadius: 12, overflow: "hidden" }}>
                <img src={form.image_url} alt="Preview" style={{ width: "100%", height: 180, objectFit: "cover" }} />
              </div>
            )}

            <div className="img-upload-zone" onClick={() => document.getElementById("listing-image-input")?.click()}>
              <span style={{ fontSize: 24, marginBottom: 6 }}>📷</span>
              <span style={{ fontSize: 13, color: "var(--t2)" }}>Click to upload an image</span>
              <span style={{ fontSize: 11, color: "var(--t3)" }}>JPG, PNG, or WebP &middot; Max 10MB</span>
            </div>
            <input
              id="listing-image-input"
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              style={{ display: "none" }}
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                if (file.size > 10 * 1024 * 1024) return;
                const formData = new FormData();
                formData.append("file", file);
                // Upload will happen after listing is created, for now show preview
                set("image_url", URL.createObjectURL(file));
              }}
            />

            <div style={{ textAlign: "center", margin: "12px 0", fontSize: 11, color: "var(--t3)" }}>or paste a URL</div>
            <label className="lp-label">
              Image URL
              <input className="lp-input" type="url" value={form.image_url || ""} onChange={(e) => set("image_url", e.target.value)} placeholder="https://..." />
            </label>
          </section>

          {mutation.isError && (
            <div className="lp-error">
              {(mutation.error as Error).message || "Something went wrong. Please try again."}
            </div>
          )}

          <button type="submit" className={`sbtn lp-submit ${mutation.isPending ? "loading" : ""}`} disabled={mutation.isPending}>
            <span className="spin" />
            <span className="slbl">{mutation.isPending ? "Publishing..." : "Publish listing"}</span>
          </button>
        </form>
      </div>
    </AgentPortalLayout>
  );
}
