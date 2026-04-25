import { useEffect, useRef, useState } from "react";
import "./App.css";

import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import { initialMessages } from "./data/fakeMessages";

function App() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm StudentNexus. I can help with F1, OPT, CPT, H1B, and student visa questions.\n\nTry asking:\n• When should I apply for OPT?\n• Can I work off campus?\n• What happens after graduation?",
      citations: []
    }
  ]);
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

const handleSend = async () => {
  const trimmed = input.trim();
  if (!trimmed || loading) return;

  const userMessage = {
    role: "user",
    content: trimmed
  };

  setMessages((prev) => [...prev, userMessage]);
  setInput("");
  setLoading(true);

  try {
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question: trimmed
      })
    });

    const data = await response.json();

    const assistantMessage = {
      role: "assistant",
      content: data.answer,
      citations: data.sources || []
    };

    setMessages((prev) => [...prev, assistantMessage]);

  } catch (error) {
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "Sorry, there was an error contacting StudentNexus.",
        citations: []
      }
    ]);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="container">
      <div className="chat-wrapper">
        <Header />

        <ChatWindow
          messages={
            loading
              ? [
                  ...messages,
                  {
                    role: "assistant",
                    loading: true,
                    content: "Thinking..."
                  }
                ]
              : messages
          }
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