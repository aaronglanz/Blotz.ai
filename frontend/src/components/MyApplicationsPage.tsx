import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMyApplications, withdrawApplication } from "../api/applications";
import Navbar from "./Navbar";

const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  Applied: { bg: "rgba(120,175,248,0.12)", color: "#4080d0", border: "rgba(120,175,248,0.3)" },
  Viewed: { bg: "rgba(240,160,96,0.12)", color: "#b07020", border: "rgba(240,160,96,0.3)" },
  Shortlisted: { bg: "rgba(77,216,138,0.12)", color: "#2a6348", border: "rgba(77,216,138,0.3)" },
  Rejected: { bg: "rgba(138,132,124,0.12)", color: "#6a6460", border: "rgba(138,132,124,0.3)" },
  Withdrawn: { bg: "rgba(138,132,124,0.12)", color: "#6a6460", border: "rgba(138,132,124,0.3)" },
};

export default function MyApplicationsPage() {
  const qc = useQueryClient();
  const appsQ = useQuery({ queryKey: ["my-applications"], queryFn: getMyApplications });
  const withdrawMutation = useMutation({
    mutationFn: withdrawApplication,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-applications"] }),
  });

  const apps = appsQ.data || [];

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>My applications</h1>
          <p className="lp-sub">Track the status of every property you've applied to.</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        {apps.length === 0 && (
          <div className="sp-empty">
            <div className="sp-empty-ico">📋</div>
            <h3>No applications yet</h3>
            <p>When you apply to a listing, it'll show up here.</p>
            <Link to="/" className="sp-empty-cta">Browse properties</Link>
          </div>
        )}

        <div className="ma-list">
          {apps.map((app) => {
            const sc = STATUS_COLORS[app.status] || STATUS_COLORS.Applied;
            return (
              <div key={app.id} className="ma-card">
                {app.listing_image_url && (
                  <div className="ma-card-img">
                    <img src={app.listing_image_url} alt={app.listing_title || ""} />
                  </div>
                )}
                <div className="ma-card-body">
                  <div className="ma-card-top">
                    <div>
                      <h3 className="ma-card-title">{app.listing_title || "Listing"}</h3>
                      <div className="ma-card-meta">
                        {app.listing_location && <span>{app.listing_location}</span>}
                        {app.agent_name && <span> &middot; {app.agent_name}</span>}
                      </div>
                      {app.listing_price && <div className="ma-card-price">{app.listing_price}</div>}
                    </div>
                    <span
                      className="ma-status-badge"
                      style={{ background: sc.bg, color: sc.color, borderColor: sc.border }}
                    >
                      {app.status}
                    </span>
                  </div>
                  <div className="ma-card-footer">
                    <span className="ma-date">Applied {new Date(app.applied_at).toLocaleDateString()}</span>
                    {app.status === "Applied" && (
                      <button
                        className="pf-doc-btn pf-doc-remove"
                        onClick={() => withdrawMutation.mutate(app.id)}
                        disabled={withdrawMutation.isPending}
                      >
                        Withdraw
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
