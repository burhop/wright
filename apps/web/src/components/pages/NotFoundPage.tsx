import { useEffect } from "react";
import { Link } from "react-router-dom";
import useLogger from "../../hooks/useLogger";

export function NotFoundPage() {
  const logger = useLogger("NotFoundPage");

  useEffect(() => {
    logger.warn("404 Page loaded", { path: window.location.pathname });
  }, [logger]);

  return (
    <div
      data-testid="page-not-found"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-xl)",
        height: "100%",
        minHeight: "400px",
        textAlign: "center",
        gap: "var(--space-md)",
      }}
    >
      <h1
        style={{
          fontSize: "4rem",
          fontFamily: "var(--font-ui)",
          color: "var(--color-error)",
        }}
      >
        404
      </h1>
      <h2
        style={{ fontFamily: "var(--font-ui)", color: "var(--color-primary)" }}
      >
        Section Not Found
      </h2>
      <p
        style={{
          fontFamily: "var(--font-body)",
          color: "var(--color-secondary)",
          maxWidth: "400px",
          marginBottom: "var(--space-lg)",
        }}
      >
        The engineering dashboard route you are attempting to visit does not
        exist or has not been wired yet.
      </p>

      <Link
        to="/"
        data-testid="back-to-dashboard-btn"
        style={{
          padding: "var(--space-md) var(--space-xl)",
          backgroundColor: "var(--color-secondary)",
          color: "var(--color-neutral)",
          fontFamily: "var(--font-ui)",
          fontWeight: "bold",
          borderRadius: "var(--radius-md)",
          transition: "background-color 0.2s ease",
        }}
      >
        Back to Dashboard
      </Link>
    </div>
  );
}

export default NotFoundPage;
