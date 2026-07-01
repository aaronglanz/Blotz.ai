import { Link, useLocation } from "react-router-dom";
import { getRenterAccount, isRenterLoggedIn } from "../renterAuth";

interface Props {
  variant?: "dark" | "light";
}

export default function Navbar({ variant = "light" }: Props) {
  const location = useLocation();
  const path = location.pathname;
  const isAgentPortal =
    path === "/list-property" ||
    path.startsWith("/agent/");

  const isDark = variant === "dark";
  const loggedIn = isRenterLoggedIn();
  const renter = getRenterAccount();

  return (
    <nav className={`nav ${isDark ? "nav-dark" : "nav-light"}`}>
      <div className="nav-inner">
        <Link to="/" className="logo">
          <span className="lmark">N</span> Nestly
        </Link>

        <div className="nav-links">
          <Link to="/" className={`nav-link ${path === "/" || path === "/search" ? "active" : ""}`}>
            Search
          </Link>
          <Link to="/saved" className={`nav-link ${path === "/saved" ? "active" : ""}`}>
            Saved
          </Link>
          <Link to="/inbox" className={`nav-link ${path === "/inbox" ? "active" : ""}`}>
            Inbox
          </Link>
          <Link to="/my-applications" className={`nav-link ${path === "/my-applications" ? "active" : ""}`}>
            Applications
          </Link>

          <span className="nav-divider" />

          {loggedIn ? (
            <Link to="/profile" className={`nav-link ${path === "/profile" ? "active" : ""}`}>
              {renter?.full_name || "Profile"}
            </Link>
          ) : (
            <>
              <Link to="/login" className={`nav-link ${path === "/login" ? "active" : ""}`}>
                Sign in
              </Link>
              <Link to="/signup" className={`nav-link ${path === "/signup" ? "active" : ""}`}>
                Sign up
              </Link>
            </>
          )}

          <span className="nav-divider" />

          <Link to="/agent" className={`nav-link ${isAgentPortal ? "active" : ""}`}>
            Agents
          </Link>
        </div>
      </div>
    </nav>
  );
}
