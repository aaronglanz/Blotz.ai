import { Link, useLocation, useNavigate } from "react-router-dom";
import { clearAgentSession, getAgentAccount } from "../agentPortal";

export default function AgentPortalNav() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const agent = getAgentAccount();

  function handleSignOut() {
    clearAgentSession();
    navigate("/agent");
  }

  return (
    <nav className="agent-nav">
      <div className="agent-nav-inner">
        <Link to="/" className="logo">
          <span className="lmark">N</span> Nestly
        </Link>

        <div className="agent-nav-links">
          <Link to="/agent" className={`agent-nav-link ${pathname === "/agent" ? "active" : ""}`}>
            Dashboard
          </Link>
          <Link
            to="/agent/listings/new"
            className={`agent-nav-link ${pathname === "/agent/listings/new" ? "active" : ""}`}
          >
            New listing
          </Link>
          <Link
            to="/agent/applications"
            className={`agent-nav-link ${pathname === "/agent/applications" ? "active" : ""}`}
          >
            Applications
          </Link>
          <Link
            to="/agent/inbox"
            className={`agent-nav-link ${pathname === "/agent/inbox" ? "active" : ""}`}
          >
            Inbox
          </Link>
        </div>

        <div className="agent-nav-actions">
          {agent ? <span className="agent-nav-meta">{agent.full_name}</span> : null}
          {agent ? (
            <button className="agent-nav-link agent-nav-button" onClick={handleSignOut}>
              Sign out
            </button>
          ) : (
            <Link to="/agent/login" className={`agent-nav-link ${pathname === "/agent/login" ? "active" : ""}`}>
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
