import { devices, type Page } from "@playwright/test";

const workspaceSurfaceTests = /workspace-surfaces\/.*\.spec\.ts/;

export const workspaceSurfaceProjects = [
  {
    name: "firefox-workspace-surfaces",
    testMatch: workspaceSurfaceTests,
    use: { ...devices["Desktop Firefox"] },
  },
  {
    name: "webkit-workspace-surfaces",
    testMatch: workspaceSurfaceTests,
    use: { ...devices["Desktop Safari"] },
  },
  {
    name: "desktop-surface",
    testMatch: workspaceSurfaceTests,
    metadata: { workspaceSurfaceHost: "desktop" },
    use: { ...devices["Desktop Chrome"] },
  },
];

export interface WorkspaceSurfaceFeatureDetection {
  desktopHost: boolean;
  webMcp: boolean;
  secureContext: boolean;
}

export async function detectWorkspaceSurfaceFeatures(
  page: Page,
): Promise<WorkspaceSurfaceFeatureDetection> {
  return page.evaluate(() => {
    const documentWithModelContext = document as Document & {
      modelContext?: unknown;
    };
    return {
      desktopHost: typeof window.wrightDesktop !== "undefined",
      webMcp: typeof documentWithModelContext.modelContext !== "undefined",
      secureContext: window.isSecureContext,
    };
  });
}
