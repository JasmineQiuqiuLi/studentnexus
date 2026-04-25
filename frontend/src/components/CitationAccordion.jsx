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
                    <strong>Source Content:</strong><br />
                    {doc.chunk_text}
                </p>

                <p>
                    <strong>Source:</strong> {doc.title}
                </p>

                {doc.section && (
                    <p>
                    <strong>Section:</strong> {doc.section}
                    </p>
                )}

                {doc.url && (
                    <p>
                    <strong>URL:</strong>{" "}
                    <a
                        href={doc.url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        Visit Source
                    </a>
                    </p>
                )}

                {doc.last_edited && (
                    <p>
                    <strong>Last Updated:</strong> {doc.last_edited}
                    </p>
                )}

                {doc.retrieved && (
                    <p>
                    <strong>Last Retrieved:</strong> {doc.retrieved}
                    </p>
                )}
                </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default CitationAccordion;