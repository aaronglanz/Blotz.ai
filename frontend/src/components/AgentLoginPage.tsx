import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import AgentPortalLayout from "./AgentPortalLayout";
import { loginAgent } from "../api/auth";
import { saveAgentSession } from "../agentPortal";

export default function AgentLoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const mutation = useMutation({
    mutationFn: loginAgent,
    onSuccess: (session) => {
      saveAgentSession(session);
      navigate("/agent/applications");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(form);
  }

  return (
    <AgentPortalLayout>
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Agent sign in</h1>
          <p className="lp-sub">
            Access your Nestly portal to publish listings, review applications, and reply to renters.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="agent-signup-grid">
          <form className="lp-form" onSubmit={handleSubmit}>
            <section className="lp-section">
              <span className="agent-kicker">Portal access</span>
              <h3 className="lp-sh">Welcome back</h3>
              <p className="lp-sh-hint">Use the email and password you created during agent onboarding.</p>

              <label className="lp-label">
                Work email
                <input
                  className="lp-input"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm((current) => ({ ...current, email: e.target.value }))}
                  placeholder="you@agency.com"
                />
              </label>

              <label className="lp-label">
                Password
                <input
                  className="lp-input"
                  type="password"
                  required
                  value={form.password}
                  onChange={(e) => setForm((current) => ({ ...current, password: e.target.value }))}
                  placeholder="Enter your password"
                />
              </label>

              {mutation.isError && (
                <div className="lp-error">
                  {(mutation.error as Error).message || "Could not sign you in."}
                </div>
              )}

              <button type="submit" className={`sbtn ${mutation.isPending ? "loading" : ""}`} disabled={mutation.isPending}>
                <span className="spin" />
                <span className="slbl">Sign in</span>
              </button>
            </section>
          </form>

          <aside className="lp-section agent-onboarding-side">
            <span className="agent-kicker">Need an account?</span>
            <div className="agent-feature-list">
              <div className="agent-feature">
                <strong>Publish listings</strong>
                <p>Create your first property and get matched to renter briefs.</p>
              </div>
              <div className="agent-feature">
                <strong>Manage renter demand</strong>
                <p>Keep applications and listing-specific conversations in one portal.</p>
              </div>
            </div>

            <Link to="/agent/signup" className="lp-back-link" style={{ marginTop: 18, display: "inline-block" }}>
              Create a new agent account
            </Link>
          </aside>
        </div>
      </div>
    </AgentPortalLayout>
  );
}
