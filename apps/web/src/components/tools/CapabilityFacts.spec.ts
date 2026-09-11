import { describe, expect, it } from "vitest";
import type { CapabilityView } from "../../services/mcp-service";
import { capabilityFacts } from "./CapabilityFacts";
import {
  emptyCapabilityFilters,
  matchesCapabilityOwnershipFilters,
  readCapabilityFilters,
} from "./CapabilityFilters";
const fixture = (
  requirements: CapabilityView["requirements"] = {},
  extra: Partial<CapabilityView> = {},
) =>
  ({
    requirements,
    tags: [],
    name: "CAD",
    vendor: "Example",
    description: "Design",
    domains: [],
    aliases: [],
    capability_summary: [],
    transport: "stdio",
    locality: "local",
    user_state: { installed: false },
    ...extra,
  }) as CapabilityView;
describe("catalog facts and filters", () => {
  it("does not equate open source with a free service", () => {
    const item = fixture({ license: "MIT", auth_model: "license-server" });
    expect(capabilityFacts(item)).toMatchObject({
      openSource: true,
      commercial: true,
      cost: "Host software license required",
    });
    expect(
      matchesCapabilityOwnershipFilters(item, {
        ...emptyCapabilityFilters,
        openSource: true,
      }),
    ).toBe(true);
    expect(
      matchesCapabilityOwnershipFilters(item, {
        ...emptyCapabilityFilters,
        commercial: true,
      }),
    ).toBe(true);
  });
  it("does not infer licensing or login from a source URL", () => {
    const facts = capabilityFacts(
      fixture(
        {},
        {
          source_records: [
            { url: "https://github.com/example/tool" },
          ] as CapabilityView["source_records"],
        },
      ),
    );
    expect(facts).toMatchObject({
      openSource: false,
      commercial: false,
      cost: "Not specified",
      login: "Not specified",
    });
  });
  it("matches any selected license category and excludes unknown licensing", () => {
    const filters = {
      ...emptyCapabilityFilters,
      openSource: true,
      commercial: true,
    };
    expect(
      matchesCapabilityOwnershipFilters(fixture({ license: "MIT" }), filters),
    ).toBe(true);
    expect(
      matchesCapabilityOwnershipFilters(
        fixture({ license: "proprietary" }),
        filters,
      ),
    ).toBe(true);
    expect(matchesCapabilityOwnershipFilters(fixture(), filters)).toBe(false);
  });
  it("uses declared OS support instead of the current computer's observation", () => {
    const item = fixture({
      supported_platforms: {
        linux_x64: { status: "yes", tested: false, notes: "Declared support" },
        windows_11_x64: { status: "no", tested: false, notes: "Unsupported" },
      },
    });
    expect(capabilityFacts(item).operatingSystems).toEqual(["linux"]);
  });
  it("distinguishes WebMCP, remote MCP, hardware, and API candidates", () => {
    expect(capabilityFacts(fixture({}, { transport: "webmcp" })).type).toBe(
      "WebMCP",
    );
    expect(capabilityFacts(fixture({}, { locality: "remote" })).location).toBe(
      "Cloud / remote server",
    );
    expect(capabilityFacts(fixture({}, { tags: ["hardware"] })).type).toBe(
      "MCP · Hardware",
    );
    expect(
      capabilityFacts(
        fixture({}, { lifecycle_stage: "verified_api_wrapper_candidate" }),
      ).type,
    ).toBe("API integration candidate");
  });
  it("preserves curated catalog filters when reading a saved URL", () => {
    expect(
      readCapabilityFilters(
        "?domain=cad&evidence_class=official_preview&platform=windows_11_x64",
      ),
    ).toEqual({
      ...emptyCapabilityFilters,
      domain: "cad",
      evidenceClass: "official_preview",
      platform: "windows_11_x64",
    });
  });
});
