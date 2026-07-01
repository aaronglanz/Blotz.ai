import { useCallback, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProfile, updateProfile, getDocuments, uploadDocument, deleteDocument } from "../api/renter";
import { checkEligible } from "../api/applications";
import Navbar from "./Navbar";
import ReadinessChecklist from "./ReadinessChecklist";
import type { RenterProfile, RenterDocument } from "../types";

const PROFILE_FIELDS: { key: keyof RenterProfile; label: string; type?: string; placeholder: string; options?: string[] }[] = [
  { key: "full_name", label: "Full name", placeholder: "e.g. Thabo Mokoena" },
  { key: "id_number", label: "SA ID number", placeholder: "e.g. 9309150000000" },
  { key: "phone", label: "Phone number", placeholder: "+27 82 123 4567" },
  { key: "email", label: "Email address", type: "email", placeholder: "you@example.com" },
  { key: "employment_status", label: "Employment status", placeholder: "", options: ["Employed", "Self-employed", "Student", "Other"] },
  { key: "monthly_income", label: "Monthly gross income (Rands)", placeholder: "e.g. R35,000" },
  { key: "employer_name", label: "Employer name", placeholder: "e.g. Acme Corp" },
];

const DOC_TYPES: { key: string; label: string; required: boolean }[] = [
  { key: "id_document", label: "South African ID document", required: true },
  { key: "bank_statement_1", label: "Bank statement (month 1)", required: true },
  { key: "bank_statement_2", label: "Bank statement (month 2)", required: true },
  { key: "bank_statement_3", label: "Bank statement (month 3)", required: true },
  { key: "payslip", label: "Proof of income / payslip", required: true },
  { key: "reference_letter", label: "Reference letter (optional)", required: false },
];

const REQUIRED_DOC_KEYS = DOC_TYPES.filter((d) => d.required).map((d) => d.key);

function getCompletionPct(profile: RenterProfile | undefined, docs: RenterDocument[]): number {
  if (!profile) return 0;
  const profileFields = ["full_name", "id_number", "phone", "email", "employment_status", "monthly_income"] as const;
  const filledFields = profileFields.filter((f) => profile[f]).length;
  const docTypes = new Set(docs.map((d) => d.document_type));
  const uploadedRequired = REQUIRED_DOC_KEYS.filter((k) => docTypes.has(k)).length;
  const total = profileFields.length + REQUIRED_DOC_KEYS.length;
  return Math.round(((filledFields + uploadedRequired) / total) * 100);
}

function isVerified(profile: RenterProfile | undefined, docs: RenterDocument[]): boolean {
  if (!profile) return false;
  const docTypes = new Set(docs.map((d) => d.document_type));
  return docTypes.has("id_document") && docTypes.has("bank_statement_1") &&
    docTypes.has("bank_statement_2") && docTypes.has("bank_statement_3") && docTypes.has("payslip");
}

function isProfileSectionComplete(profile: RenterProfile | undefined): boolean {
  if (!profile) return false;
  return !!(profile.full_name && profile.id_number && profile.phone && profile.email &&
    profile.employment_status && profile.monthly_income);
}

function isDocsSectionComplete(docs: RenterDocument[]): boolean {
  const docTypes = new Set(docs.map((d) => d.document_type));
  return REQUIRED_DOC_KEYS.every((k) => docTypes.has(k));
}

export default function ProfilePage() {
  const [searchParams] = useSearchParams();
  const qc = useQueryClient();
  const profileQ = useQuery({ queryKey: ["renter-profile"], queryFn: getProfile });
  const docsQ = useQuery({ queryKey: ["renter-documents"], queryFn: getDocuments });
  const eligibilityQ = useQuery({ queryKey: ["eligibility"], queryFn: checkEligible });
  const [form, setForm] = useState<Partial<RenterProfile>>({});
  const [dirty, setDirty] = useState(false);
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [uploadingType, setUploadingType] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const profile = profileQ.data;
  const docs = docsQ.data || [];

  const saveMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["renter-profile"] });
      qc.invalidateQueries({ queryKey: ["eligibility"] });
      setDirty(false);
      setMessage("Profile saved");
      setTimeout(() => setMessage(null), 2000);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ type, file }: { type: string; file: File }) => uploadDocument(type, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["renter-documents"] });
      qc.invalidateQueries({ queryKey: ["eligibility"] });
      setUploadingType(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["renter-documents"] });
      qc.invalidateQueries({ queryKey: ["eligibility"] });
    },
  });

  const handleChange = useCallback((key: string, val: string) => {
    setForm((f) => ({ ...f, [key]: val }));
    setDirty(true);
  }, []);

  function handleSave() {
    saveMutation.mutate(form);
  }

  function handleFileSelect(docType: string, file: File) {
    setFileError(null);
    if (file.size > 10 * 1024 * 1024) {
      setFileError("File too large. Maximum 10MB.");
      return;
    }
    setUploadingType(docType);
    uploadMutation.mutate({ type: docType, file });
  }

  const pct = getCompletionPct(profile, docs);
  const verified = isVerified(profile, docs);
  const profileComplete = isProfileSectionComplete(profile);
  const docsComplete = isDocsSectionComplete(docs);

  // Merge profile data with local form state
  const merged = { ...profile, ...form };

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Your renter profile</h1>
          <p className="lp-sub">Complete your profile to instantly apply to any listing on Nestly.</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        {searchParams.get("msg") === "complete" && (
          <div className="pf-toast" style={{ marginBottom: 18 }}>
            Finish the checklist below to unlock instant apply for every saved home and search result.
          </div>
        )}

        {searchParams.get("return") && (
          <div style={{ marginBottom: 18 }}>
            <Link className="lp-back-link" to={searchParams.get("return") || "/"}>
              Return to your shortlist
            </Link>
          </div>
        )}

        <ReadinessChecklist eligibility={eligibilityQ.data} />

        {/* Progress bar */}
        <div className="pf-progress-wrap">
          <div className="pf-progress-bar">
            <div className="pf-progress-fill" style={{ width: `${pct}%` }} />
          </div>
          <div className="pf-progress-row">
            <span className="pf-progress-pct">{pct}% complete</span>
            {verified && <span className="pf-verified-badge">Pre-Verified &#10003;</span>}
          </div>
        </div>

        {message && <div className="pf-toast">{message}</div>}

        {/* Personal details */}
        <section className="lp-section">
          <div className="pf-section-hdr">
            <h3 className="lp-sh">Personal details</h3>
            {profileComplete && <span className="pf-tick">&#10003;</span>}
          </div>
          <p className="lp-sh-hint">This information is shared with agents only when they shortlist you.</p>

          {PROFILE_FIELDS.map((f) => (
            <label key={f.key} className="lp-label">
              {f.label}
              {f.options ? (
                <select
                  className="lp-input"
                  value={(merged as Record<string, string | null>)[f.key] || ""}
                  onChange={(e) => handleChange(f.key, e.target.value)}
                >
                  <option value="">Select...</option>
                  {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input
                  className="lp-input"
                  type={f.type || "text"}
                  value={(merged as Record<string, string | null>)[f.key] || ""}
                  onChange={(e) => handleChange(f.key, e.target.value)}
                  placeholder={f.placeholder}
                />
              )}
            </label>
          ))}

          <button
            className={`sbtn ${saveMutation.isPending ? "loading" : ""}`}
            onClick={handleSave}
            disabled={!dirty || saveMutation.isPending}
            style={{ marginTop: 8 }}
          >
            <span className="spin" />
            <span className="slbl">{saveMutation.isPending ? "Saving..." : "Save profile"}</span>
          </button>
        </section>

        {/* Documents */}
        <section className="lp-section">
          <div className="pf-section-hdr">
            <h3 className="lp-sh">Documents</h3>
            {docsComplete && <span className="pf-tick">&#10003;</span>}
          </div>
          <p className="lp-sh-hint">
            Upload PDF or image files (max 10MB each). Documents are stored securely and never shared
            with agents until you submit an application.
          </p>

          {fileError && <div className="lp-error" style={{ marginBottom: 14 }}>{fileError}</div>}
          {uploadMutation.isError && <div className="lp-error" style={{ marginBottom: 14 }}>{(uploadMutation.error as Error).message || "Upload failed. Please try again."}</div>}

          <div className="pf-doc-list">
            {DOC_TYPES.map((dt) => {
              const existing = docs.find((d) => d.document_type === dt.key);
              const isUploading = uploadingType === dt.key && uploadMutation.isPending;
              return (
                <div key={dt.key} className={`pf-doc-row ${existing ? "uploaded" : ""}`}>
                  <div className="pf-doc-info">
                    <span className="pf-doc-status">{existing ? "&#10003;" : "&#9675;"}</span>
                    <div>
                      <strong>{dt.label}</strong>
                      {existing && <span className="pf-doc-file">{existing.file_name}</span>}
                    </div>
                  </div>
                  <div className="pf-doc-actions">
                    {existing && (
                      <button
                        className="pf-doc-btn pf-doc-remove"
                        onClick={() => deleteMutation.mutate(existing.id)}
                      >
                        Remove
                      </button>
                    )}
                    <button
                      className="pf-doc-btn"
                      onClick={() => fileRefs.current[dt.key]?.click()}
                      disabled={isUploading}
                    >
                      {isUploading ? "Uploading..." : existing ? "Replace" : "Upload"}
                    </button>
                    <input
                      ref={(el) => { fileRefs.current[dt.key] = el; }}
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileSelect(dt.key, file);
                        e.target.value = "";
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
