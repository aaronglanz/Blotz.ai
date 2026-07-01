import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAgentApplications, updateApplicationStatus, getAgentDocuments } from "../api/applications";
import AgentPortalLayout from "./AgentPortalLayout";
import type { ApplicationForAgent } from "../types";

const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  Applied: { bg: "rgba(120,175,248,0.12)", color: "#4080d0", border: "rgba(120,175,248,0.3)" },
  Viewed: { bg: "rgba(240,160,96,0.12)", color: "#b07020", border: "rgba(240,160,96,0.3)" },
  Shortlisted: { bg: "rgba(77,216,138,0.12)", color: "#2a6348", border: "rgba(77,216,138,0.3)" },
  Rejected: { bg: "rgba(138,132,124,0.12)", color: "#6a6460", border: "rgba(138,132,124,0.3)" },
};

export default function AgentApplicationsPage() {
  const qc = useQueryClient();
  const appsQ = useQuery({ queryKey: ["agent-applications"], queryFn: getAgentApplications });
  const [expandedApp, setExpandedApp] = useState<string | null>(null);
  const [docs, setDocs] = useState<Record<string, { id: string; document_type: string; file_name: string }[]>>({});

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateApplicationStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent-applications"] }),
  });

  async function handleExpand(app: ApplicationForAgent) {
    if (expandedApp === app.id) {
      setExpandedApp(null);
      return;
    }
    setExpandedApp(app.id);
    if (!docs[app.id]) {
      const appDocs = await getAgentDocuments(app.id);
      setDocs((d) => ({ ...d, [app.id]: appDocs }));
    }
    // Auto-mark as Viewed if currently Applied
    if (app.status === "Applied") {
      statusMutation.mutate({ id: app.id, status: "Viewed" });
    }
  }

  const apps = appsQ.data || [];
  const newCount = apps.filter((a) => a.status === "Applied").length;

  return (
    <AgentPortalLayout requireAuth>
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Applicant review</h1>
          <p className="lp-sub">Review renter applications for your listed properties.</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        {apps.length === 0 && (
          <div className="sp-empty">
            <div className="sp-empty-ico">📬</div>
            <h3>No applications yet</h3>
            <p>When renters apply to your listings, they'll appear here.</p>
          </div>
        )}

        <div className="ag-list">
          {apps.map((app) => {
            const sc = STATUS_COLORS[app.status] || STATUS_COLORS.Applied;
            const isExpanded = expandedApp === app.id;
            const appDocs = docs[app.id] || [];
            return (
              <div key={app.id} className={`ag-card ${isExpanded ? "expanded" : ""}`}>
                <div className="ag-card-header" onClick={() => handleExpand(app)}>
                  <div className="ag-card-info">
                    <strong>{app.renter_name || "Renter"}</strong>
                    <span className="ag-card-sub">
                      {app.listing_title} &middot; {app.listing_location}
                    </span>
                  </div>
                  <div className="ag-card-right">
                    {app.is_verified && <span className="pf-verified-badge" style={{ fontSize: 11 }}>Pre-Verified &#10003;</span>}
                    <span
                      className="ma-status-badge"
                      style={{ background: sc.bg, color: sc.color, borderColor: sc.border }}
                    >
                      {app.status}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="ag-card-detail">
                    <div className="ag-detail-grid">
                      <div className="ag-detail-item">
                        <span className="ag-detail-label">Employment</span>
                        <span>{app.renter_employment || "—"}</span>
                      </div>
                      <div className="ag-detail-item">
                        <span className="ag-detail-label">Monthly income</span>
                        <span>{app.renter_income || "—"}</span>
                      </div>
                      <div className="ag-detail-item">
                        <span className="ag-detail-label">ID number</span>
                        <span>{app.renter_id_masked || "—"}</span>
                      </div>
                      {app.status === "Shortlisted" && (
                        <>
                          <div className="ag-detail-item">
                            <span className="ag-detail-label">Phone</span>
                            <span>{app.renter_phone || "—"}</span>
                          </div>
                          <div className="ag-detail-item">
                            <span className="ag-detail-label">Email</span>
                            <span>{app.renter_email || "—"}</span>
                          </div>
                        </>
                      )}
                      {app.status !== "Shortlisted" && (
                        <div className="ag-detail-item ag-detail-locked">
                          <span className="ag-detail-label">Contact details</span>
                          <span>Shortlist to reveal phone &amp; email</span>
                        </div>
                      )}
                    </div>

                    {appDocs.length > 0 && (
                      <div className="ag-docs">
                        <span className="ag-detail-label" style={{ marginBottom: 8, display: "block" }}>Documents</span>
                        {appDocs.map((d) => (
                          <a
                            key={d.id}
                            href={`/api/renter/documents/${d.id}/download?agent_id=self`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ag-doc-link"
                          >
                            {d.document_type.replace(/_/g, " ")} — {d.file_name}
                          </a>
                        ))}
                      </div>
                    )}

                    <div className="ag-actions">
                      {app.status !== "Shortlisted" && (
                        <button
                          className="sbtn"
                          onClick={() => statusMutation.mutate({ id: app.id, status: "Shortlisted" })}
                          disabled={statusMutation.isPending}
                        >
                          <span className="slbl">Shortlist</span>
                        </button>
                      )}
                      {app.status !== "Rejected" && (
                        <button
                          className="pf-doc-btn pf-doc-remove"
                          onClick={() => statusMutation.mutate({ id: app.id, status: "Rejected" })}
                          disabled={statusMutation.isPending}
                        >
                          Reject
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AgentPortalLayout>
  );
}
