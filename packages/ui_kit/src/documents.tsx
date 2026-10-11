import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** A passive view of already-scoped bytes; document references grant no reads. */
export function MarkdownDocument({ text }: { text: string }) {
  return (
    <div className="wp-document">
      <article className="wp-markdown" aria-label="Document contents">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          skipHtml
          components={{
            a: ({ children }) => <span className="wp-document-reference">{children}</span>,
            img: ({ alt }) => <span className="wp-muted">[Image: {alt || "see source"}]</span>,
            table: ({ children }) => <div className="wp-table"><table>{children}</table></div>,
          }}
        >
          {text}
        </ReactMarkdown>
      </article>
      <details className="wp-document-source">
        <summary>View source</summary>
        <pre className="wp-text">{text}</pre>
      </details>
    </div>
  );
}
