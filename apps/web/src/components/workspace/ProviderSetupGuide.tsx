import { useEffect, useId, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./provider-setup-guide.css";

export function ProviderSetupGuide({ text }: { text: string }) {
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    setOpen(false);
  }, [text]);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open && !node.open) node.showModal();
    else if (!open && node.open) node.close();
    return () => {
      if (node.open) node.close();
    };
  }, [open]);
  return (
    <>
      <button
        type="button"
        className="provider-setup-guide-button"
        onClick={() => setOpen(true)}
      >
        Read provider setup guide (bundled copy)
      </button>
      <dialog
        ref={dialog}
        className="provider-setup-guide-dialog"
        aria-labelledby={`${id}-title`}
        onCancel={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setOpen(false);
        }}
        onClose={(event) => {
          event.stopPropagation();
          setOpen(false);
        }}
      >
        <header>
          <h2 id={`${id}-title`}>Provider setup guide</h2>
          <button type="button" onClick={() => setOpen(false)}>
            Back to setup
          </button>
        </header>
        {open && (
          <div className="provider-setup-guide-dialog__body">
            <p>
              This bundled copy retains its dated evidence and limitations. It
              does not establish readiness on this computer. Repository paths
              are shown as references.
            </p>
            <article className="markdown-viewer-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                skipHtml
                components={{
                  a: ({ href, children }) =>
                    href && /^https?:\/\//i.test(href) ? (
                      <a href={href} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    ) : (
                      <span>
                        {children}
                        {href && (
                          <>
                            {" "}
                            (<code>{href}</code>)
                          </>
                        )}
                      </span>
                    ),
                  img: ({ alt }) => <span>{alt ?? "Guide illustration"}</span>,
                }}
              >
                {text}
              </ReactMarkdown>
            </article>
            <details>
              <summary>Original plain text</summary>
              <pre>{text}</pre>
            </details>
          </div>
        )}
      </dialog>
    </>
  );
}
