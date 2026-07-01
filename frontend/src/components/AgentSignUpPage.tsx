import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import AgentPortalLayout from "./AgentPortalLayout";
import { saveAgentSession } from "../agentPortal";
import { signUpAgent } from "../api/auth";

export default function AgentSignUpPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    password_confirm: "",
    phone: "",
    agency_name: "",
  });

  const mutation = useMutation({
    mutationFn: signUpAgent,
    onSuccess: (session) => {
      saveAgentSession(session);
      navigate("/agent/listings/new");
    },
  });

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  const [passwordError, setPasswordError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password !== form.password_confirm) {
      setPasswordError("Passwords do not match");
      return;
    }
    setPasswordError("");
    const { password_confirm: _, ...submitData } = form;
    mutation.mutate(submitData);
  }

  return (
    <AgentPortalLayout>
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Create your agent account</h1>
          <p className="lp-sub">
            Register to publish properties on Nestly, manage renter applications,
            and reply to leads inside your agent portal.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="agent-signup-grid">
          <form className="lp-form" onSubmit={handleSubmit}>
            <section className="lp-section">
              <span className="agent-kicker">Agent registration</span>
              <h3 className="lp-sh">Your details</h3>
              <p className="lp-sh-hint">
                This creates your portal access before you publish your first property.
              </p>

              <label className="lp-label">
                Full name
                <input
                  className="lp-input"
                  required
                  value={form.full_name}
                  onChange={(e) => set("full_name", e.target.value)}
                  placeholder="e.g. Thandi Jacobs"
                />
              </label>

              <label className="lp-label">
                Work email
                <input
                  className="lp-input"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  placeholder="you@agency.com"
                />
              </label>

              <div className="lp-row">
                <label className="lp-label">
                  Password
                  <input
                    className="lp-input"
                    type="password"
                    required
                    minLength={6}
                    value={form.password}
                    onChange={(e) => set("password", e.target.value)}
                    placeholder="Create a secure password"
                  />
                </label>

                <label className="lp-label">
                  Confirm password
                  <input
                    className="lp-input"
                    type="password"
                    required
                    value={form.password_confirm}
                    onChange={(e) => set("password_confirm", e.target.value)}
                    placeholder="Confirm your password"
                  />
                </label>
              </div>
              {passwordError && <div className="lp-error">{passwordError}</div>}

              <div className="lp-row">
                <label className="lp-label">
                  Phone number
                  <input
                    className="lp-input"
                    type="tel"
                    required
                    value={form.phone}
                    onChange={(e) => set("phone", e.target.value)}
                    placeholder="+27 82 123 4567"
                  />
                </label>

                <label className="lp-label">
                  Agency name
                  <input
                    className="lp-input"
                    required
                    value={form.agency_name}
                    onChange={(e) => set("agency_name", e.target.value)}
                    placeholder="e.g. Atlantic Living"
                  />
                </label>
              </div>

              {mutation.isError && (
                <div className="lp-error">
                  {(mutation.error as Error).message || "Could not create your account."}
                </div>
              )}

              <button type="submit" className={`sbtn ${mutation.isPending ? "loading" : ""}`} disabled={mutation.isPending}>
                <span className="spin" />
                <span className="slbl">Create account &amp; continue</span>
              </button>
            </section>
          </form>

          <aside className="lp-section agent-onboarding-side">
            <span className="agent-kicker">After signup</span>
            <div className="agent-feature-list">
              <div className="agent-feature">
                <strong>Publish listings</strong>
                <p>Create your first property immediately after registration.</p>
              </div>
              <div className="agent-feature">
                <strong>Manage applications</strong>
                <p>Review shortlisted renters and keep your pipeline organized.</p>
              </div>
              <div className="agent-feature">
                <strong>Chat with renters</strong>
                <p>Respond from a dedicated inbox attached to each listing.</p>
              </div>
            </div>

            <Link to="/agent/login" className="lp-back-link" style={{ marginTop: 18, display: "inline-block" }}>
              Already have an account? Sign in
            </Link>
          </aside>
        </div>
      </div>
    </AgentPortalLayout>
  );
}
