import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { signUpRenter } from "../api/auth";
import { saveRenterSession } from "../renterAuth";
import Navbar from "./Navbar";

export default function RenterSignUpPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });

  const mutation = useMutation({
    mutationFn: signUpRenter,
    onSuccess: (session) => {
      saveRenterSession(session);
      navigate("/profile");
    },
  });

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(form);
  }

  return (
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Create your account</h1>
          <p className="lp-sub">
            Sign up to save homes, build your renter profile, and instantly apply to listings.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="agent-signup-grid">
          <form className="lp-form" onSubmit={handleSubmit}>
            <section className="lp-section">
              <span className="agent-kicker">Renter account</span>
              <h3 className="lp-sh">Your details</h3>
              <p className="lp-sh-hint">
                Create an account to unlock saving, messaging, and instant apply.
              </p>

              <label className="lp-label">
                Full name
                <input
                  className="lp-input"
                  required
                  value={form.full_name}
                  onChange={(e) => set("full_name", e.target.value)}
                  placeholder="e.g. Thabo Mokoena"
                />
              </label>

              <label className="lp-label">
                Email
                <input
                  className="lp-input"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  placeholder="you@example.com"
                />
              </label>

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

              {mutation.isError && (
                <div className="lp-error">
                  {(mutation.error as Error).message || "Could not create your account."}
                </div>
              )}

              <button type="submit" className={`sbtn ${mutation.isPending ? "loading" : ""}`} disabled={mutation.isPending}>
                <span className="spin" />
                <span className="slbl">Create account</span>
              </button>
            </section>
          </form>

          <aside className="lp-section agent-onboarding-side">
            <span className="agent-kicker">Why sign up?</span>
            <div className="agent-feature-list">
              <div className="agent-feature">
                <strong>Save &amp; compare</strong>
                <p>Keep a shortlist of homes you love and compare them side by side.</p>
              </div>
              <div className="agent-feature">
                <strong>Instant apply</strong>
                <p>Build your verified profile once, then apply to any listing with one click.</p>
              </div>
              <div className="agent-feature">
                <strong>Message agents</strong>
                <p>Ask questions about viewings, pets, lease terms before you commit.</p>
              </div>
            </div>

            <Link to="/login" className="lp-back-link" style={{ marginTop: 18, display: "inline-block" }}>
              Already have an account? Sign in
            </Link>
          </aside>
        </div>
      </div>
    </div>
  );
}
