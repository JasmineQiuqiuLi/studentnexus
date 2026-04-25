function CitationAccordion({ citations, messageIndex, openDocs, onToggleDoc }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="doc-list">
      {citations.map((doc, docIndex) => {
        const key = `${messageIndex}-${docIndex}`;
        const isOpen = openDocs[key];

        return (
          <div key={key} className="doc-item">
            <div
            className="doc-header"
            onClick={() => onToggleDoc(key)}
            >
            <span className={isOpen ? "chevron open" : "chevron"}></span>
            <span>{doc.title}</span>
            </div>

            {isOpen && (
              <div className="doc-body">
                <p>
                  <strong>Chunk:</strong> {doc.chunk_text}
                </p>
                <p>
                  <strong>Document:</strong> {doc.doc_id}
                </p>
                <p>
                  <strong>Chunk ID:</strong> {doc.chunk_id}
                </p>
                <p>
                  <strong>Rank:</strong> {doc.rank}
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default CitationAccordion;