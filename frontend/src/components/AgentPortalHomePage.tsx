import { Link } from "react-router-dom";
import AgentPortalLayout from "./AgentPortalLayout";

export default function AgentPortalHomePage() {
  return (
    <AgentPortalLayout>
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>List with Nestly</h1>
          <p className="lp-sub">
            Join the agent portal to publish properties, manage renter applications,
            and reply to qualified leads from one focused workspace.
          </p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="agent-onboarding-grid">
          <section className="lp-section agent-onboarding-main">
            <span className="agent-kicker">Agent onboarding</span>
            <h3 className="lp-sh">What happens next</h3>
            <div className="agent-steps">
              <div className="agent-step">
                <strong>1. Create your agent account</strong>
                <p>Set up your identity and agency details so renters know who they are speaking to.</p>
              </div>
              <div className="agent-step">
                <strong>2. Publish your first property</strong>
                <p>Add your listing details, photos, availability, and the lifestyle cues that improve matching.</p>
              </div>
              <div className="agent-step">
                <strong>3. Review and respond to leads</strong>
                <p>Track renter applications and answer questions inside your dedicated agent portal.</p>
              </div>
            </div>

            <div className="agent-cta-row">
              <Link to="/agent/signup" className="sbtn">
                <span className="slbl">Create agent account &amp; continue</span>
              </Link>
              <Link to="/agent/login" className="lp-back-link">
                I already have access
              </Link>
            </div>
          </section>

          <aside className="lp-section agent-onboarding-side">
            <span className="agent-kicker">Inside the portal</span>
            <div className="agent-feature-list">
              <div className="agent-feature">
                <strong>Listings</strong>
                <p>Publish and refine your property inventory.</p>
              </div>
              <div className="agent-feature">
                <strong>Applications</strong>
                <p>Review qualified renters and shortlist the strongest matches.</p>
              </div>
              <div className="agent-feature">
                <strong>Inbox</strong>
                <p>Keep listing-specific conversations with renters in one place.</p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AgentPortalLayout>
  );
}
