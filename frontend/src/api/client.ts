import axios from "axios";
import { getAgentSession } from "../agentPortal";
import { getRenterSession } from "../renterAuth";

function getUserId(): string {
  let id = localStorage.getItem("nestly_user_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("nestly_user_id", id);
  }
  return id;
}

const client = axios.create({
  baseURL: "/api",
});

client.interceptors.request.use((config) => {
  const agentSession = getAgentSession();
  const renterSession = getRenterSession();
  const session = agentSession || renterSession;

  config.headers["X-User-Id"] = session?.user.id || getUserId();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      const msg = error.response.data.detail;
      return Promise.reject(new Error(typeof msg === "string" ? msg : JSON.stringify(msg)));
    }
    return Promise.reject(error);
  },
);

export { getUserId };
export default client;
