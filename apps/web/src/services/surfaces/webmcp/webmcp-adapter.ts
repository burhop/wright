import {
  WrightSurfaceSdk,
  type WrightSurfaceRegistration,
  type WrightSurfaceTool,
} from "./wright-surface-sdk";

interface NativeModelContext {
  registerTool(
    tool: {
      name: string;
      description: string;
      inputSchema: Readonly<Record<string, unknown>>;
      execute: (
        argumentsValue: Readonly<Record<string, unknown>>,
        options?: { signal?: AbortSignal },
      ) => unknown;
    },
    options: { signal: AbortSignal },
  ): Promise<void>;
}

interface NativeDocument extends Document {
  readonly modelContext?: NativeModelContext;
  readonly permissionsPolicy?: { allowsFeature(name: string): boolean };
}

export type NativeWebMcpState = "absent" | "available" | "policy_denied";

export function detectNativeWebMcp(
  documentValue: Document = document,
): NativeWebMcpState {
  const candidate = documentValue as NativeDocument;
  if (typeof candidate.modelContext?.registerTool !== "function")
    return "absent";
  if (candidate.permissionsPolicy?.allowsFeature("tools") === false)
    return "policy_denied";
  return "available";
}

export async function registerWebMcpTool(
  tool: WrightSurfaceTool,
  options: {
    sdk?: WrightSurfaceSdk;
    document?: Document;
    dualRegisterNative?: boolean;
  } = {},
): Promise<
  WrightSurfaceRegistration & {
    readonly nativeState: NativeWebMcpState | "rejected";
  }
> {
  const sdk = options.sdk || new WrightSurfaceSdk();
  const stable = await sdk.registerTool(tool);
  const documentValue = (options.document || document) as NativeDocument;
  const detected = detectNativeWebMcp(documentValue);
  let nativeState: NativeWebMcpState | "rejected" = detected;
  const lifetime = new AbortController();
  const abortNative = () => lifetime.abort(tool.signal.reason);
  tool.signal.addEventListener("abort", abortNative, { once: true });
  if (tool.signal.aborted) abortNative();
  if (options.dualRegisterNative && detected === "available") {
    try {
      await documentValue.modelContext!.registerTool(
        {
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema,
          execute: (argumentsValue, callOptions) => {
            const signal = callOptions?.signal
              ? AbortSignal.any([lifetime.signal, callOptions.signal])
              : lifetime.signal;
            signal.throwIfAborted();
            return tool.handler(argumentsValue, { signal });
          },
        },
        { signal: lifetime.signal },
      );
    } catch {
      nativeState = "rejected";
    }
  }
  let disposal: Promise<void> | undefined;
  return {
    nativeState,
    dispose: () => {
      if (!disposal) {
        lifetime.abort();
        tool.signal.removeEventListener("abort", abortNative);
        disposal = stable.dispose();
      }
      return disposal;
    },
  };
}
