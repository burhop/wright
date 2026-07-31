import {
  WrightSurfaceSdk,
  type WrightSurfaceRegistration,
  type WrightSurfaceTool,
} from "./wright-surface-sdk";

interface NativeModelContext {
  registerTool(tool: {
    name: string;
    description: string;
    inputSchema: Readonly<Record<string, unknown>>;
    execute: (argumentsValue: Readonly<Record<string, unknown>>) => unknown;
  }): Promise<{ unregister?: () => void | Promise<void> } | void>;
}

interface NativeDocument extends Document {
  readonly modelContext?: NativeModelContext;
  readonly permissionsPolicy?: { allowsFeature(name: string): boolean };
}

export type NativeWebMcpState = "absent" | "available" | "policy_denied";

export function detectNativeWebMcp(documentValue: Document = document): NativeWebMcpState {
  const candidate = documentValue as NativeDocument;
  if (typeof candidate.modelContext?.registerTool !== "function") return "absent";
  if (candidate.permissionsPolicy?.allowsFeature("tools") === false) return "policy_denied";
  return "available";
}

export async function registerWebMcpTool(
  tool: WrightSurfaceTool,
  options: { sdk?: WrightSurfaceSdk; document?: Document; dualRegisterNative?: boolean } = {},
): Promise<WrightSurfaceRegistration & { readonly nativeState: NativeWebMcpState | "rejected" }> {
  const sdk = options.sdk || new WrightSurfaceSdk();
  const stable = await sdk.registerTool(tool);
  const documentValue = (options.document || document) as NativeDocument;
  const detected = detectNativeWebMcp(documentValue);
  let nativeState: NativeWebMcpState | "rejected" = detected;
  let nativeHandle: { unregister?: () => void | Promise<void> } | void;
  if (options.dualRegisterNative && detected === "available") {
    try {
      nativeHandle = await documentValue.modelContext!.registerTool({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
        execute: (argumentsValue) => tool.handler(argumentsValue, { signal: tool.signal }),
      });
    } catch {
      nativeState = "rejected";
    }
  }
  return {
    nativeState,
    dispose: async () => {
      await nativeHandle?.unregister?.();
      await stable.dispose();
    },
  };
}
