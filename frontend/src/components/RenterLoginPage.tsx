import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { loginRenter } from "../api/auth";
import { saveRenterSession } from "../renterAuth";
import Navbar from "./Navbar";

export default function RenterLoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const returnTo = params.get("return") || "/";
  const [form, setForm] = useState({ email: "", password: "" });

  const mutation = useMutation({
    mutationFn: loginRenter,
    onSuccess: (session) => {
      saveRenterSession(session);
      navigate(returnTo);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(form);
  }

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Welcome back</h1>
          <p className="lp-sub">
            Sign in to access your saved homes, applications, and messages.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="agent-signup-grid">
          <form className="lp-form" onSubmit={handleSubmit}>
            <section className="lp-section">
              <span className="agent-kicker">Sign in</span>
              <h3 className="lp-sh">Your account</h3>
              <p className="lp-sh-hint">Use the email and password you signed up with.</p>

              <label className="lp-label">
                Email
                <input
                  className="lp-input"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  placeholder="you@example.com"
                />
              </label>

              <label className="lp-label">
                Password
                <input
                  className="lp-input"
                  type="password"
                  required
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
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
            <span className="agent-kicker">New to Nestly?</span>
            <div className="agent-feature-list">
              <div className="agent-feature">
                <strong>AI-powered search</strong>
                <p>Describe your dream home in natural language and let our AI find matches.</p>
              </div>
              <div className="agent-feature">
                <strong>Verified profile</strong>
                <p>Upload your documents once and apply to any listing instantly.</p>
              </div>
            </div>

            <Link to="/signup" className="lp-back-link" style={{ marginTop: 18, display: "inline-block" }}>
              Create a new account
            </Link>
          </aside>
        </div>
      </div>
    </div>
  );
}
