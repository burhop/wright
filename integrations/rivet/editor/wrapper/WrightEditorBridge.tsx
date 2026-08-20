import { QueryClient } from '@tanstack/react-query';
import {
  deserializeProject,
  serializeProject,
  type AttachedData,
  type Project,
} from '@valerypopoff/rivet2-core';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  RivetAppHost,
  type RivetAppHostActiveProjectChangedEvent,
  type RivetWorkspaceHost,
} from './host.js';
import {
  MemoryStorage,
  createWrightEnvironmentProvider,
  createWrightAiFetch,
  loadWrightAiConfig,
  seedWrightAiStorage,
  type WrightAiConfig,
} from './WrightAiRuntime.js';

type WrightRequest =
  | {
      type: 'wright-rivet:set-project';
      requestId?: string;
      project: string;
      path?: string;
    }
  | {
      type: 'wright-rivet:get-project';
      requestId?: string;
    }
  | {
      type: 'wright-rivet:set-run-state';
      requestId?: string;
      runId?: string;
      steps?: Array<{ nodeId?: string | null; state?: string; label?: string }>;
    }
  | {
      type: 'wright-rivet:clear-run-state';
      requestId?: string;
    }
  | {
      type: 'wright-rivet:focus-node';
      requestId?: string;
      nodeId?: string;
    }
  | {
      type: 'wright-rivet:focus-canvas';
      requestId?: string;
    };

const RUN_STATES = new Set(['queued', 'running', 'cancelling', 'cancelled', 'succeeded', 'failed']);

type ActiveProject = {
  project: Omit<Project, 'data'>;
  data?: Project['data'];
};

function trustedParentOrigin(): string | null {
  const configured = new URLSearchParams(window.location.search).get('parentOrigin');
  if (!configured) return null;

  try {
    const parsed = new URL(configured);
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.origin !== configured) {
      return null;
    }
    return parsed.origin;
  } catch {
    return null;
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'The Rivet canvas request failed.';
}

export function WrightEditorBridge() {
  const [queryClient] = useState(() => new QueryClient());
  const [storage] = useState(() => new MemoryStorage());
  const [workspaceHost, setWorkspaceHost] = useState<RivetWorkspaceHost | null>(null);
  const [aiConfig, setAiConfig] = useState<WrightAiConfig | null>(null);
  const activeProject = useRef<ActiveProject | null>(null);
  const attachedData = useRef<AttachedData>({});
  const hasOpenedProject = useRef(false);
  const expectedParentOrigin = useMemo(trustedParentOrigin, []);

  useEffect(() => {
    let active = true;
    const originalFetch = window.fetch;
    const bridgedFetch = createWrightAiFetch(originalFetch.bind(window), window.location.origin);
    window.fetch = bridgedFetch;
    void (async () => {
      const config = await loadWrightAiConfig();
      await seedWrightAiStorage(storage, config);
      if (active) setAiConfig(config);
    })();
    return () => {
      active = false;
      if (window.fetch === bridgedFetch) window.fetch = originalFetch;
    };
  }, [storage]);

  const postToWright = useCallback(
    (message: Record<string, unknown>) => {
      if (window.parent === window || expectedParentOrigin === null) return;
      window.parent.postMessage(message, expectedParentOrigin);
    },
    [expectedParentOrigin],
  );

  const onActiveProjectChanged = useCallback(
    (event: RivetAppHostActiveProjectChangedEvent) => {
      if (event.project) {
        activeProject.current = { project: event.project, data: event.data };
      } else if (!hasOpenedProject.current) {
        activeProject.current = null;
      }
    },
    [],
  );

  useEffect(() => {
    if (!workspaceHost || expectedParentOrigin === null || window.parent === window) return;

    const respondWithError = (requestId: string | undefined, code: string, error: unknown) => {
      postToWright({
        type: 'wright-rivet:error',
        requestId,
        code,
        message: errorMessage(error),
      });
    };

    const handleMessage = (event: MessageEvent<unknown>) => {
      if (event.source !== window.parent) return;
      if (event.origin !== expectedParentOrigin) return;
      if (!event.data || typeof event.data !== 'object') return;

      const message = event.data as Partial<WrightRequest>;
      if (message.type === 'wright-rivet:set-project') {
        if (typeof message.project !== 'string') {
          respondWithError(message.requestId, 'INVALID_PROJECT', new Error('Project payload must be a string.'));
          return;
        }

        void (async () => {
          try {
            const [project, nextAttachedData] = deserializeProject(message.project, message.path ?? null);
            const snapshot = {
              project,
              data: project.data,
              path: message.path ?? null,
            };
            const opened = hasOpenedProject.current
              ? await workspaceHost.replaceCurrent(snapshot)
              : await workspaceHost.openProjectSnapshot(snapshot);
            if (!opened) {
              throw new Error('Rivet rejected the workspace project without replacing the current canvas.');
            }
            hasOpenedProject.current = true;
            activeProject.current = { project, data: project.data };
            attachedData.current = nextAttachedData;
            postToWright({
              type: 'wright-rivet:project-set',
              requestId: message.requestId,
              projectId: project.metadata.id,
            });
          } catch (error) {
            respondWithError(message.requestId, 'PROJECT_OPEN_FAILED', error);
          }
        })();
        return;
      }

      if (message.type === 'wright-rivet:get-project') {
        try {
          const current = activeProject.current;
          if (!current) throw new Error('No Wright workspace project is open.');
          const serialized = serializeProject(
            { ...current.project, data: current.data } as Project,
            attachedData.current,
          );
          postToWright({
            type: 'wright-rivet:project',
            requestId: message.requestId,
            project: String(serialized),
          });
        } catch (error) {
          respondWithError(message.requestId, 'PROJECT_SERIALIZE_FAILED', error);
        }
        return;
      }

      if (message.type === 'wright-rivet:set-run-state') {
        if (!Array.isArray(message.steps) || message.steps.length > 500) {
          respondWithError(message.requestId, 'INVALID_RUN_STATE', new Error('Run state must contain at most 500 steps.'));
          return;
        }
        const steps = message.steps
          .filter(
            (step): step is { nodeId: string; state: string; label?: string } =>
              !!step &&
              typeof step.nodeId === 'string' &&
              step.nodeId.length > 0 &&
              step.nodeId.length <= 200 &&
              typeof step.state === 'string' &&
              RUN_STATES.has(step.state),
          )
          .map((step) => ({ nodeId: step.nodeId, state: step.state, label: step.label?.slice(0, 200) }));
        workspaceHost.setWrightRunState(steps);
        postToWright({ type: 'wright-rivet:run-state-set', requestId: message.requestId, count: steps.length });
        return;
      }

      if (message.type === 'wright-rivet:clear-run-state') {
        workspaceHost.clearWrightRunState();
        postToWright({ type: 'wright-rivet:run-state-cleared', requestId: message.requestId });
        return;
      }

      if (message.type === 'wright-rivet:focus-node') {
        if (typeof message.nodeId !== 'string' || !message.nodeId || message.nodeId.length > 200) {
          respondWithError(message.requestId, 'INVALID_NODE_ID', new Error('Node identity is invalid.'));
          return;
        }
        const found = workspaceHost.focusWrightNode(message.nodeId);
        postToWright({ type: 'wright-rivet:node-focused', requestId: message.requestId, nodeId: message.nodeId, found });
        return;
      }

      if (message.type === 'wright-rivet:focus-canvas') {
        workspaceHost.focusWrightCanvas();
        postToWright({ type: 'wright-rivet:canvas-focused', requestId: message.requestId });
      }
    };

    window.addEventListener('message', handleMessage);
    postToWright({ type: 'wright-rivet:ready', protocolVersion: 3 });
    return () => window.removeEventListener('message', handleMessage);
  }, [expectedParentOrigin, postToWright, workspaceHost]);

  useEffect(() => {
    if (!aiConfig) return;
    postToWright({
      type: 'wright-rivet:ai-status',
      available: aiConfig.available,
      reason: aiConfig.available ? undefined : aiConfig.reason,
    });
  }, [aiConfig, postToWright]);

  if (!aiConfig) {
    return <div data-testid="rivet-ai-loading">Connecting Rivet AI…</div>;
  }

  return (
    <RivetAppHost
      queryClient={queryClient}
      providers={{ storage, environment: createWrightEnvironmentProvider(aiConfig) }}
      ui={{
        canvasOnly: true,
        fileMenu: { visibleItems: [] },
        webApps: { desktopPreview: false },
      }}
      loadingFallback={<div data-testid="rivet-canvas-loading">Loading graph canvas…</div>}
      onActiveProjectChanged={onActiveProjectChanged}
      onWorkspaceHostReady={setWorkspaceHost}
      onWorkspaceHostDisposed={() => setWorkspaceHost(null)}
      onOpenError={({ error }) =>
        postToWright({
          type: 'wright-rivet:error',
          code: 'PROJECT_OPEN_FAILED',
          message: errorMessage(error),
        })
      }
    />
  );
}
