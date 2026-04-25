import { useEffect, useRef, useState } from "react";
import "./App.css";

import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import { initialMessages } from "./data/fakeMessages";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  const [openDocs, setOpenDocs] = useState({});

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleDoc = (key) => {
    setOpenDocs((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSend = () => {
    const trimmedInput = input.trim();
    if (!trimmedInput) return;

    const newUserMessage = {
      role: "user",
      content: trimmedInput
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
  };

  return (
    <div className="container">
      <div className="chat-wrapper">
        <Header />

        <ChatWindow
          messages={messages}
          bottomRef={bottomRef}
          openDocs={openDocs}
          onToggleDoc={toggleDoc}
        />

        <InputBar input={input} setInput={setInput} onSend={handleSend} />
      </div>
    </div>
  );
}

export default App;