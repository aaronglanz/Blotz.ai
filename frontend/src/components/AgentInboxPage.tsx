import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  getAgentConversations,
  getConversation,
  sendConversationMessage,
} from "../api/conversations";
import AgentPortalLayout from "./AgentPortalLayout";

export default function AgentInboxPage() {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [draft, setDraft] = useState("");
  const selectedConversationId = params.get("conversation");

  const conversationsQ = useQuery({
    queryKey: ["agent-conversations"],
    queryFn: getAgentConversations,
  });

  useEffect(() => {
    if (!selectedConversationId && conversationsQ.data && conversationsQ.data.length > 0) {
      setParams({ conversation: conversationsQ.data[0].id });
    }
  }, [selectedConversationId, conversationsQ.data, setParams]);

  const conversationQ = useQuery({
    queryKey: ["conversation", selectedConversationId],
    queryFn: () => getConversation(selectedConversationId!),
    enabled: !!selectedConversationId,
  });

  const sendMutation = useMutation({
    mutationFn: (body: string) => sendConversationMessage(selectedConversationId!, body),
    onSuccess: async () => {
      setDraft("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["agent-conversations"] }),
        queryClient.invalidateQueries({ queryKey: ["conversation", selectedConversationId] }),
      ]);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !selectedConversationId) return;
    sendMutation.mutate(draft);
  }

  return (
    <AgentPortalLayout requireAuth>
      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Agent inbox</h1>
          <p className="lp-sub">Reply to renter questions in the context of the listing they&apos;re asking about.</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="inbox-layout">
          <aside className="inbox-sidebar">
            <h3>Renter conversations</h3>
            {conversationsQ.data?.length ? (
              conversationsQ.data.map((conversation) => (
                <button
                  key={conversation.id}
                  className={`inbox-thread${selectedConversationId === conversation.id ? " active" : ""}`}
                  onClick={() => setParams({ conversation: conversation.id })}
                >
                  <strong>{conversation.listing_title}</strong>
                  <span>{conversation.counterpart_name || "Renter"}</span>
                  <p>{conversation.last_message_preview || "No messages yet"}</p>
                  {conversation.unread_count > 0 && <em>{conversation.unread_count} new</em>}
                </button>
              ))
            ) : (
              <div className="sp-empty mini">
                <div className="sp-empty-ico">📭</div>
                <h3>No renter messages yet</h3>
                <p>New renter questions from listings will appear here.</p>
              </div>
            )}
          </aside>

          <section className="inbox-panel">
            {conversationQ.data ? (
              <>
                <div className="inbox-header">
                  <div>
                    <h3>{conversationQ.data.listing_title}</h3>
                    <p>{conversationQ.data.counterpart_name || "Renter"} · {conversationQ.data.listing_location}</p>
                  </div>
                  <span className="readiness-badge">{conversationQ.data.listing_price}</span>
                </div>

                <div className="inbox-messages">
                  {conversationQ.data.messages.map((message) => (
                    <div
                      key={message.id}
                      className={`inbox-message${message.sender_user_id === conversationQ.data?.counterpart_user_id ? "" : " self"}`}
                    >
                      <p>{message.body}</p>
                      <span>{new Date(message.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>

                <form className="inbox-compose" onSubmit={handleSubmit}>
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Reply with viewing info, lease terms, parking details..."
                    rows={3}
                  />
                  <button className={`sbtn ${sendMutation.isPending ? "loading" : ""}`} disabled={sendMutation.isPending}>
                    <span className="spin" />
                    <span className="slbl">Send reply</span>
                  </button>
                </form>
              </>
            ) : (
              <div className="sp-empty">
                <div className="sp-empty-ico">💬</div>
                <h3>Select a renter conversation</h3>
                <p>Each thread stays attached to the listing it belongs to.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </AgentPortalLayout>
  );
}
