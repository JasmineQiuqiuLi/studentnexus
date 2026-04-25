function InputBar({ input, setInput, onSend }) {
  return (
    <div className="input-bar">
      <textarea
        rows="1"
        placeholder="Ask a question..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
      />

      <button onClick={onSend}>Send</button>
    </div>
  );
}

export default InputBar;