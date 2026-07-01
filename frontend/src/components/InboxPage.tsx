import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  getConversation,
  getMyConversations,
  sendConversationMessage,
} from "../api/conversations";
import Navbar from "./Navbar";

export default function InboxPage() {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [draft, setDraft] = useState("");
  const selectedConversationId = params.get("conversation");

  const conversationsQ = useQuery({
    queryKey: ["conversations"],
    queryFn: getMyConversations,
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
        queryClient.invalidateQueries({ queryKey: ["conversations"] }),
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
    <div className="lp-page">
      <Navbar />

      <div className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Your inbox</h1>
          <p className="lp-sub">Ask agents questions before you apply and keep every listing conversation in one place.</p>
        </div>
        <div className="lp-hero-fade" />
      </div>

      <div className="lp-body">
        <div className="inbox-layout">
          <aside className="inbox-sidebar">
            <h3>Conversations</h3>
            {conversationsQ.data?.length ? (
              conversationsQ.data.map((conversation) => (
                <button
                  key={conversation.id}
                  className={`inbox-thread${selectedConversationId === conversation.id ? " active" : ""}`}
                  onClick={() => setParams({ conversation: conversation.id })}
                >
                  <strong>{conversation.listing_title}</strong>
                  <span>{conversation.counterpart_name || "Agent"}</span>
                  <p>{conversation.last_message_preview || "No messages yet"}</p>
                  {conversation.unread_count > 0 && <em>{conversation.unread_count} new</em>}
                </button>
              ))
            ) : (
              <div className="sp-empty mini">
                <div className="sp-empty-ico">✉️</div>
                <h3>No conversations yet</h3>
                <p>Start a conversation from a saved home or search result.</p>
              </div>
            )}
          </aside>

          <section className="inbox-panel">
            {conversationQ.data ? (
              <>
                <div className="inbox-header">
                  <div>
                    <h3>{conversationQ.data.listing_title}</h3>
                    <p>{conversationQ.data.listing_location} · {conversationQ.data.listing_price}</p>
                  </div>
                  <span className="readiness-badge">{conversationQ.data.counterpart_name || "Agent"}</span>
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
                    placeholder="Ask about availability, viewings, pets, lease terms..."
                    rows={3}
                  />
                  <button className={`sbtn ${sendMutation.isPending ? "loading" : ""}`} disabled={sendMutation.isPending}>
                    <span className="spin" />
                    <span className="slbl">Send message</span>
                  </button>
                </form>
              </>
            ) : (
              <div className="sp-empty">
                <div className="sp-empty-ico">💬</div>
                <h3>Select a conversation</h3>
                <p>Your latest listing conversation will appear here.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
