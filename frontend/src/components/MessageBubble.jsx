import CitationAccordion from "./CitationAccordion";

function MessageBubble({ message, index, openDocs, onToggleDoc }) {
  const isUser = message.role === "user";

  return (
    <div className={isUser ? "message-row user-row" : "message-row assistant-row"}>
      <div className={isUser ? "message user-message" : "message assistant-message"}>
        <div>{message.content}</div>

        {!isUser && (
          <CitationAccordion
            citations={message.citations}
            messageIndex={index}
            openDocs={openDocs}
            onToggleDoc={onToggleDoc}
          />
        )}
      </div>
    </div>
  );
}

export default MessageBubble;