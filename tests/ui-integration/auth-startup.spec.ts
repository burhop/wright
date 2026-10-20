import { expect, test } from "@playwright/test";

test("protected initialization waits for unlock and survives reload", async ({
  page,
}) => {
  let authenticated = false;
  const premature: string[] = [];
  const observed = new Set<string>();
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/session/status") {
      return route.fulfill({ json: { auth_required: true, authenticated } });
    }
    if (path === "/api/auth/session") {
      if (route.request().postDataJSON().token !== "test-local-token") {
        return route.fulfill({
          status: 401,
          json: { detail: "Invalid access token" },
        });
      }
      authenticated = true;
      return route.fulfill({ status: 204 });
    }
    if (!authenticated) {
      premature.push(path);
      return route.fulfill({
        status: 401,
        json: { detail: "Authentication required" },
      });
    }
    observed.add(path);
    const responses: Record<string, unknown> = {
      "/api/settings": { theme: "dark", llm_provider: "hermes" },
      "/api/agent/sessions": { sessions: [] },
      "/api/mcp/servers": { servers: [] },
      "/api/mcp/tools": { tools: [] },
      "/api/workspace/recent": { workspaces: [] },
      "/api/workspace/list": { workspaces: [] },
      "/api/setup/status": { is_configured: true, active_agent: "hermes" },
    };
    return route.fulfill({ json: responses[path] ?? [] });
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Unlock Wright" }),
  ).toBeVisible();
  await expect(page.getByText(/Docker container/)).toHaveCount(0);
  expect(premature).toEqual([]);
  expect(observed.size).toBe(0);
  await page.getByLabel("Access Token").fill("wrong");
  await page.getByRole("button", { name: "Unlock", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  expect(premature).toEqual([]);
  await page.getByLabel("Access Token").fill("test-local-token");
  await page.getByRole("button", { name: "Unlock", exact: true }).click();
  await expect(page.getByTestId("page-dashboard")).toBeVisible();
  await expect
    .poll(() => [...observed])
    .toEqual(
      expect.arrayContaining([
        "/api/settings",
        "/api/agent/sessions",
        "/api/mcp/servers",
        "/api/mcp/tools",
      ]),
    );
  await page.reload();
  await expect(page.getByTestId("page-dashboard")).toBeVisible();
  expect(premature).toEqual([]);
});
