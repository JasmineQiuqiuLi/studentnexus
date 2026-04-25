import MessageBubble from "./MessageBubble";

function ChatWindow({ messages, bottomRef, openDocs, onToggleDoc }) {
  return (
    <div className="chat-window">
      {messages.map((message, index) => (
        <MessageBubble
          key={index}
          message={message}
          index={index}
          openDocs={openDocs}
          onToggleDoc={onToggleDoc}
        />
      ))}

      <div ref={bottomRef}></div>
    </div>
  );
}

export default ChatWindow;