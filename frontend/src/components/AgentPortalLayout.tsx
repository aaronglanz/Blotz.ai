import type { ReactNode } from "react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AgentPortalNav from "./AgentPortalNav";
import { hasAgentAccount } from "../agentPortal";

interface Props {
  children: ReactNode;
  requireAuth?: boolean;
}

export default function AgentPortalLayout({ children, requireAuth = false }: Props) {
  const navigate = useNavigate();

  useEffect(() => {
    if (requireAuth && !hasAgentAccount()) {
      navigate("/agent/login", { replace: true });
    }
  }, [navigate, requireAuth]);

  return (
    <div className="lp-page">
      <AgentPortalNav />
      {children}
    </div>
  );
}
