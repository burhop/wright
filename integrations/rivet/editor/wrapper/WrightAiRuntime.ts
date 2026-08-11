export interface WrightStorage {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export class MemoryStorage implements WrightStorage {
  readonly #values = new Map<string, string>();

  async getItem(key: string): Promise<string | null> {
    return this.#values.get(key) ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.#values.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.#values.delete(key);
  }
}

export type WrightAiConfig =
  | {
      available: true;
      provider: 'custom';
      model: 'wright-hermes';
      baseUrl: string;
      token: string;
      expiresAt: string;
    }
  | { available: false; reason: string };

export async function loadWrightAiConfig(
  fetchConfig: typeof fetch = fetch,
): Promise<WrightAiConfig> {
  try {
    const response = await fetchConfig('/wright-ai/config', {
      cache: 'no-store',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return { available: false, reason: 'bridge_unavailable' };
    const value = (await response.json()) as Partial<WrightAiConfig>;
    if (value.available !== true) {
      return {
        available: false,
        reason:
          'reason' in value && typeof value.reason === 'string'
            ? value.reason
            : 'hermes_unavailable',
      };
    }
    if (
      value.provider !== 'custom' ||
      value.model !== 'wright-hermes' ||
      typeof value.baseUrl !== 'string' ||
      !value.baseUrl.startsWith('/') ||
      typeof value.token !== 'string' ||
      value.token.length < 16 ||
      typeof value.expiresAt !== 'string'
    ) {
      return { available: false, reason: 'bridge_config_invalid' };
    }
    return value as WrightAiConfig;
  } catch {
    return { available: false, reason: 'bridge_unavailable' };
  }
}

export async function seedWrightAiStorage(
  storage: WrightStorage,
  config: WrightAiConfig,
  editorOrigin = globalThis.location?.origin,
): Promise<void> {
  if (!config.available) {
    await storage.removeItem('ai');
    return;
  }
  await storage.setItem(
    'ai',
    JSON.stringify({
      selectAssistModel: 'custom',
      // The AI SDK's OpenAI-compatible provider requires an absolute URL even
      // when fetch itself could resolve this same-origin path. Keep the host
      // contract origin-relative, then bind it to the editor origin here.
      aiAssistCustomProviderBaseURL: editorOrigin
        ? new URL(config.baseUrl, editorOrigin).toString().replace(/\/$/, '')
        : config.baseUrl,
      aiAssistCustomModel: config.model,
    }),
  );
}

export function createWrightEnvironmentProvider(
  config: WrightAiConfig,
  fetchConfig: typeof fetch = fetch,
) {
  let currentConfig = config;
  return {
    async getEnvVar(name: string): Promise<string | undefined> {
      if (!['CUSTOM_PROVIDER_API_KEY', 'CUSTOM_AI_API_KEY'].includes(name)) {
        return undefined;
      }
      currentConfig = await loadWrightAiConfig(fetchConfig);
      if (!currentConfig.available) return undefined;
      return currentConfig.token;
    },
  };
}
