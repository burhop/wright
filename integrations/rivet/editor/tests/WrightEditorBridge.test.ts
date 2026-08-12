import assert from 'node:assert/strict';
import test from 'node:test';

import {
  MemoryStorage,
  createWrightAiFetch,
  createWrightEnvironmentProvider,
  loadWrightAiConfig,
  seedWrightAiStorage,
  type WrightAiConfig,
} from '../wrapper/WrightAiRuntime.ts';

const available: WrightAiConfig = {
  available: true,
  provider: 'custom',
  model: 'wright-hermes',
  baseUrl: '/wright-ai/v1',
  token: 'ephemeral-browser-token-value',
  expiresAt: '2099-08-05T22:00:00Z',
};

test('seeds only the exact Rivet AI hybrid-storage keys with an absolute provider URL', async () => {
  const storage = new MemoryStorage();
  await seedWrightAiStorage(storage, available, 'http://127.0.0.1:9180');
  assert.deepEqual(JSON.parse((await storage.getItem('ai'))!), {
    selectAssistModel: 'custom',
    aiAssistCustomProviderBaseURL: 'http://127.0.0.1:9180/wright-ai/v1',
    aiAssistCustomModel: 'wright-hermes',
  });
  assert.equal(await storage.getItem('settings'), null);
  assert.equal(await storage.getItem('openAiApiKey'), null);
});

test('keeps the ephemeral credential in the runtime environment provider', async () => {
  const provider = createWrightEnvironmentProvider(
    available,
    async () => new Response(JSON.stringify(available)),
  );
  assert.equal(await provider.getEnvVar('CUSTOM_PROVIDER_API_KEY'), available.token);
  assert.equal(await provider.getEnvVar('OPENAI_API_KEY'), undefined);
  assert.equal(JSON.stringify(JSON.parse(JSON.stringify(available))).includes('hermes-secret'), false);
});

test('refreshes the short-lived browser credential before provider use', async () => {
  const refreshed = {
    ...available,
    token: 'refreshed-ephemeral-browser-token',
  };
  const provider = createWrightEnvironmentProvider(
    available,
    async () => new Response(JSON.stringify(refreshed)),
  );

  assert.equal(
    await provider.getEnvVar('CUSTOM_PROVIDER_API_KEY'),
    refreshed.token,
  );
});

test('reports unavailable config without inventing provider or key controls', async () => {
  const config = await loadWrightAiConfig(async () =>
    new Response(JSON.stringify({ available: false, reason: 'hermes_unavailable' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  assert.deepEqual(config, { available: false, reason: 'hermes_unavailable' });
  const storage = new MemoryStorage();
  await seedWrightAiStorage(storage, config);
  assert.equal(await storage.getItem('ai'), null);
  assert.equal(await createWrightEnvironmentProvider(config).getEnvVar('CUSTOM_PROVIDER_API_KEY'), undefined);
});

test('moves only same-origin Wright AI bearer credentials to the surface-safe header', async () => {
  const requests: Request[] = [];
  const bridgedFetch = createWrightAiFetch(
    async (input) => {
      requests.push(new Request(input));
      return new Response('{}');
    },
    'http://127.0.0.1:5173',
  );

  await bridgedFetch('http://127.0.0.1:5173/wright-ai/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: 'Bearer short-lived-token' },
    body: '{}',
  });
  await bridgedFetch('https://example.test/v1/chat/completions', {
    headers: { Authorization: 'Bearer external-token' },
  });

  assert.equal(requests[0].headers.get('Authorization'), null);
  assert.equal(requests[0].headers.get('X-Rivet-AI-Token'), 'short-lived-token');
  assert.equal(requests[1].headers.get('Authorization'), 'Bearer external-token');
  assert.equal(requests[1].headers.get('X-Rivet-AI-Token'), null);
});

test('bridges the Vite development surface route used by the embedded editor', async () => {
  let request: Request | undefined;
  const bridgedFetch = createWrightAiFetch(
    async (input) => {
      request = new Request(input);
      return new Response('{}');
    },
    'http://127.0.0.1:5173',
  );

  await bridgedFetch(
    'http://127.0.0.1:5173/__wright-surface/127.0.0.1%3A64151/wright-ai/v1/chat/completions',
    { headers: { Authorization: 'Bearer development-token' } },
  );

  assert.equal(request?.headers.get('Authorization'), null);
  assert.equal(request?.headers.get('X-Rivet-AI-Token'), 'development-token');
});
