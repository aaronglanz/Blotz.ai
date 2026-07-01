import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import App from "./App";
import ListPropertyPage from "./components/ListPropertyPage";
import ProfilePage from "./components/ProfilePage";
import MyApplicationsPage from "./components/MyApplicationsPage";
import AgentApplicationsPage from "./components/AgentApplicationsPage";
import SavedHomesPage from "./components/SavedHomesPage";
import InboxPage from "./components/InboxPage";
import AgentInboxPage from "./components/AgentInboxPage";
import AgentPortalHomePage from "./components/AgentPortalHomePage";
import AgentSignUpPage from "./components/AgentSignUpPage";
import AgentLoginPage from "./components/AgentLoginPage";
import RenterSignUpPage from "./components/RenterSignUpPage";
import RenterLoginPage from "./components/RenterLoginPage";
import ListingDetailPage from "./components/ListingDetailPage";
import "./styles/variables.css";
import "./styles/app.css";

function NotFoundPage() {
  return (
    <div className="lp-page">
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <div className="not-found">
            <h1>404</h1>
            <h2>Page not found</h2>
            <p>The page you're looking for doesn't exist or has been moved.</p>
            <a href="/" className="sbtn" style={{ display: "inline-flex" }}>
              <span className="slbl">Back to Nestly</span>
            </a>
          </div>
        </div>
        <div className="lp-hero-fade" />
      </div>
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/search" element={<Navigate to="/" replace />} />
          <Route path="/signup" element={<RenterSignUpPage />} />
          <Route path="/login" element={<RenterLoginPage />} />
          <Route path="/saved" element={<SavedHomesPage />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/list-property" element={<Navigate to="/agent" replace />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/my-applications" element={<MyApplicationsPage />} />
          <Route path="/agent" element={<AgentPortalHomePage />} />
          <Route path="/agent/signup" element={<AgentSignUpPage />} />
          <Route path="/agent/login" element={<AgentLoginPage />} />
          <Route path="/agent/listings/new" element={<ListPropertyPage />} />
          <Route path="/agent/applications" element={<AgentApplicationsPage />} />
          <Route path="/agent/inbox" element={<AgentInboxPage />} />
          <Route path="/listings/:id" element={<ListingDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
