import {
  agentService,
  type AgentThinkingLevel,
} from "../../../services/agent-service";

import type { PromptRequestOutputKind } from "../domain/prompt-request-routing";

export type DiagnosticThinkingLevel = "default" | AgentThinkingLevel;

export interface DiagnosticLlmModelOption {
  value: string;
  label: string;
  provider: string;
  model: string;
  isCurrent: boolean;
}

export interface DiagnosticLlmModelGroup {
  provider: string;
  label: string;
  options: readonly DiagnosticLlmModelOption[];
}

export interface DiagnosticLlmRequestImage {
  name: string;
  dataUrl: string;
}

export interface DiagnosticLlmRequestDocument {
  name: string;
  mediaType: string;
  text: string | null;
}

export interface DiagnosticLlmRequest {
  prompt: string;
  output: PromptRequestOutputKind;
  images: readonly DiagnosticLlmRequestImage[];
  documents: readonly DiagnosticLlmRequestDocument[];
  responseInstructions?: string;
}

export interface DiagnosticLlmSettings {
  model: DiagnosticLlmModelOption;
  thinkingLevel: DiagnosticThinkingLevel;
}

export interface DiagnosticLlmResult {
  text: string;
  provider: string;
  model: string;
  thinkingLevel: DiagnosticThinkingLevel;
}

export type DiagnosticLlmProgressStage =
  "preparing" | "uploading" | "waiting" | "generating" | "finalizing";

export interface DiagnosticLlmProgress {
  stage: DiagnosticLlmProgressStage;
  message: string;
  partialText: string;
  observedAt: number;
}

export interface DiagnosticLlmExecutionObserver {
  onProgress(progress: DiagnosticLlmProgress): void;
}

export interface DiagnosticLlmAdapter {
  listModels(): Promise<readonly DiagnosticLlmModelGroup[]>;
  execute(
    request: DiagnosticLlmRequest,
    settings: DiagnosticLlmSettings,
    observer?: DiagnosticLlmExecutionObserver,
  ): Promise<DiagnosticLlmResult>;
}

function reportProgress(
  observer: DiagnosticLlmExecutionObserver | undefined,
  stage: DiagnosticLlmProgressStage,
  message: string,
  partialText = "",
): void {
  observer?.onProgress({
    stage,
    message,
    partialText,
    observedAt: Date.now(),
  });
}

function responsePrompt(request: DiagnosticLlmRequest): string {
  const documentContext = request.documents
    .filter(({ text }) => text !== null)
    .map(
      ({ name, mediaType, text }) =>
        `\n\nDocument: ${name} (${mediaType})\n${text ?? ""}`,
    )
    .join("");
  return [
    "Complete this isolated workflow AI task without calling tools.",
    request.responseInstructions ??
      "Interpret the supplied request and return a concise candidate design brief as plain text.\nState important assumptions and identify missing information instead of inventing facts.",
    "",
    request.prompt,
    request.output === "request" ? documentContext : "",
  ].join("\n");
}

async function imageFileFromDataUrl(
  image: DiagnosticLlmRequestImage,
): Promise<File> {
  const response = await fetch(image.dataUrl);
  const blob = await response.blob();
  return new File([blob], image.name, {
    type: blob.type || "image/png",
  });
}

export const wrightDiagnosticLlmAdapter: DiagnosticLlmAdapter = {
  async listModels() {
    const catalog = await agentService.listHermesModels();
    return catalog.groups.map((group) => ({
      provider: group.provider,
      label: group.label,
      options: group.options.map((option) => ({
        value: option.value,
        label: option.label,
        provider: option.provider,
        model: option.model,
        isCurrent: option.is_current,
      })),
    }));
  },

  async execute(request, settings, observer) {
    if (request.output !== "request" && request.output !== "text") {
      throw new Error(
        "This AI task accepts a complete request or text instructions, not an isolated artifact collection.",
      );
    }

    reportProgress(
      observer,
      "preparing",
      "Creating an isolated AI execution session.",
    );
    const session = await agentService.createSession();
    try {
      const imageIds: string[] = [];
      if (request.output === "request") {
        for (const [index, image] of request.images.entries()) {
          reportProgress(
            observer,
            "uploading",
            `Uploading image ${index + 1} of ${request.images.length}: ${image.name}`,
          );
          const uploaded = await agentService.uploadFile(
            await imageFileFromDataUrl(image),
          );
          imageIds.push(uploaded.file_id);
        }
      }

      reportProgress(
        observer,
        "waiting",
        `Waiting for ${settings.model.label} to begin responding.`,
      );
      let text = "";
      let lastPublishedAt = 0;
      let lastPublishedLength = 0;
      for await (const event of agentService.sendMessage(
        session.sessionId,
        responsePrompt(request),
        imageIds,
        undefined,
        {
          thinkingLevel:
            settings.thinkingLevel === "default"
              ? undefined
              : settings.thinkingLevel,
          toolPolicy: "none",
          modelSelection: {
            provider: settings.model.provider,
            model: settings.model.model,
            requireLock: true,
          },
        },
      )) {
        if (event.type === "token") {
          text += event.text;
          const now = Date.now();
          if (
            now - lastPublishedAt >= 120 ||
            text.length - lastPublishedLength >= 160
          ) {
            reportProgress(
              observer,
              "generating",
              "Receiving model output. Preview is not committed yet.",
              text,
            );
            lastPublishedAt = now;
            lastPublishedLength = text.length;
          }
        }
        if (event.type === "tool") {
          throw new Error(
            `The no-tools AI boundary was violated by tool call ${event.name}.`,
          );
        }
        if (event.type === "error") throw new Error(event.message);
      }

      if (!text.trim()) {
        throw new Error("The selected model returned no text output.");
      }
      reportProgress(
        observer,
        "finalizing",
        "Validating the completed text and cleaning up the AI session.",
        text,
      );
      return {
        text: text.trim(),
        provider: settings.model.provider,
        model: settings.model.model,
        thinkingLevel: settings.thinkingLevel,
      };
    } finally {
      await agentService
        .deleteSession(session.sessionId)
        .catch(() => undefined);
    }
  },
};

const deterministicModel: DiagnosticLlmModelOption = {
  value: "deterministic::fixture",
  label: "Deterministic fixture",
  provider: "deterministic",
  model: "fixture",
  isCurrent: true,
};

export const deterministicDiagnosticLlmAdapter: DiagnosticLlmAdapter = {
  async listModels() {
    return [
      {
        provider: "deterministic",
        label: "Offline test",
        options: [deterministicModel],
      },
    ];
  },
  async execute(request, settings, observer) {
    reportProgress(
      observer,
      "generating",
      "Producing deterministic fixture output.",
    );
    const text = `Candidate brief created from ${request.prompt.length} prompt characters, ${request.output === "request" ? request.images.length : 0} routed images, and ${request.output === "request" ? request.documents.length : 0} routed documents. Missing dimensions remain assumptions requiring review.`;
    reportProgress(
      observer,
      "finalizing",
      "Deterministic fixture output is ready for validation.",
      text,
    );
    return {
      text,
      provider: settings.model.provider,
      model: settings.model.model,
      thinkingLevel: settings.thinkingLevel,
    };
  },
};
