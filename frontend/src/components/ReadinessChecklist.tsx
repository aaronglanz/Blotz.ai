import type { EligibilityCheck } from "../types";

const PROFILE_LABELS: Record<string, string> = {
  full_name: "Full name",
  id_number: "SA ID number",
  phone: "Phone number",
  email: "Email address",
  employment_status: "Employment status",
  monthly_income: "Monthly income",
};

const DOCUMENT_LABELS: Record<string, string> = {
  id_document: "South African ID document",
  bank_statement_1: "Bank statement (month 1)",
  bank_statement_2: "Bank statement (month 2)",
  bank_statement_3: "Bank statement (month 3)",
  payslip: "Proof of income / payslip",
};

interface Props {
  eligibility: EligibilityCheck | undefined;
  compact?: boolean;
}

export default function ReadinessChecklist({ eligibility, compact = false }: Props) {
  if (!eligibility) return null;
  const missingProfile = eligibility.missing_profile_fields;
  const missingDocs = eligibility.missing_documents;

  if (eligibility.eligible) {
    return (
      <div className={`readiness-card${compact ? " compact" : ""}`}>
        <div className="readiness-top">
          <strong>Application ready</strong>
          <span className="readiness-badge ok">Ready</span>
        </div>
        <p>Your renter profile and required documents are complete, so you can apply instantly.</p>
      </div>
    );
  }

  return (
    <div className={`readiness-card${compact ? " compact" : ""}`}>
      <div className="readiness-top">
        <strong>Complete these before you apply</strong>
        <span className="readiness-badge">Incomplete</span>
      </div>
      <p>Nestly will send a stronger application once these basics are in place.</p>
      {missingProfile.length > 0 && (
        <div className="readiness-group">
          <span className="readiness-label">Profile details</span>
          <div className="readiness-list">
            {missingProfile.map((field) => (
              <span key={field} className="readiness-item">
                {PROFILE_LABELS[field] || field}
              </span>
            ))}
          </div>
        </div>
      )}
      {missingDocs.length > 0 && (
        <div className="readiness-group">
          <span className="readiness-label">Required documents</span>
          <div className="readiness-list">
            {missingDocs.map((field) => (
              <span key={field} className="readiness-item">
                {DOCUMENT_LABELS[field] || field}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
