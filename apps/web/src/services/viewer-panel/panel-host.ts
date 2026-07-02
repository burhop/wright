import type { PanelHost, Event, Disposable } from "./types";

export class PanelHostImpl implements PanelHost, Disposable {
  readonly id: string;
  public title: string;
  readonly container: HTMLElement;
  private _active: boolean;
  private _visible: boolean;

  private viewStateListeners = new Set<
    (e: { active: boolean; visible: boolean }) => void
  >();
  private disposeListeners = new Set<() => void>();
  private messageListeners = new Set<(e: unknown) => void>();
  private messageHandlerDisposable: Disposable;

  private pingInterval: any = null;
  private pongTimeout: any = null;
  private _isUnresponsive = false;
  private unresponsiveListeners = new Set<() => void>();
  private responsiveListeners = new Set<() => void>();

  constructor(
    id: string,
    title: string,
    container: HTMLElement,
    active = true,
    visible = true,
  ) {
    this.id = id;
    this.title = title;
    this.container = container;
    this._active = active;
    this._visible = visible;

    const handleMessage = (event: MessageEvent) => {
      const iframe = this.container.querySelector("iframe");
      if (iframe && event.source === iframe.contentWindow) {
        let data = event.data;
        if (typeof data === "string") {
          try {
            data = JSON.parse(data);
          } catch {
            // Keep original string if parsing fails
          }
        }

        if (
          data &&
          typeof data === "object" &&
          "type" in data &&
          data.type === "pong"
        ) {
          this.handlePong();
        }

        for (const listener of this.messageListeners) {
          listener(data);
        }
      }
    };

    window.addEventListener("message", handleMessage);
    this.messageHandlerDisposable = {
      dispose: () => {
        window.removeEventListener("message", handleMessage);
      },
    };

    this.startHeartbeat();
  }

  get active(): boolean {
    return this._active;
  }

  get visible(): boolean {
    return this._visible;
  }

  setViewState(active: boolean, visible: boolean) {
    if (this._active !== active || this._visible !== visible) {
      this._active = active;
      this._visible = visible;
      for (const listener of this.viewStateListeners) {
        listener({ active, visible });
      }
    }
  }

  readonly onDidChangeViewState: Event<{ active: boolean; visible: boolean }> =
    (listener) => {
      this.viewStateListeners.add(listener);
      return {
        dispose: () => {
          this.viewStateListeners.delete(listener);
        },
      };
    };

  readonly onDidDispose: Event<void> = (listener) => {
    this.disposeListeners.add(listener);
    return {
      dispose: () => {
        this.disposeListeners.delete(listener);
      },
    };
  };

  readonly onDidReceiveMessage: Event<unknown> = (listener) => {
    this.messageListeners.add(listener);
    return {
      dispose: () => {
        this.messageListeners.delete(listener);
      },
    };
  };

  readonly onDidBecomeUnresponsive: Event<void> = (listener) => {
    this.unresponsiveListeners.add(listener);
    return {
      dispose: () => {
        this.unresponsiveListeners.delete(listener);
      },
    };
  };

  readonly onDidBecomeResponsive: Event<void> = (listener) => {
    this.responsiveListeners.add(listener);
    return {
      dispose: () => {
        this.responsiveListeners.delete(listener);
      },
    };
  };

  postMessage(message: unknown): void {
    const iframe = this.container.querySelector("iframe");
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage(message, "*");
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      const iframe = this.container.querySelector("iframe");
      if (!iframe) return;

      this.postMessage({ type: "ping" });

      this.pongTimeout = setTimeout(() => {
        if (!this._isUnresponsive) {
          this._isUnresponsive = true;
          for (const l of this.unresponsiveListeners) {
            l();
          }
        }
      }, 1000);
    }, 2000);
  }

  private stopHeartbeat() {
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.pongTimeout) clearTimeout(this.pongTimeout);
  }

  private handlePong() {
    if (this.pongTimeout) clearTimeout(this.pongTimeout);
    if (this._isUnresponsive) {
      this._isUnresponsive = false;
      for (const l of this.responsiveListeners) {
        l();
      }
    }
  }

  dispose(): void {
    this.stopHeartbeat();
    this.messageHandlerDisposable.dispose();
    for (const listener of this.disposeListeners) {
      listener();
    }
    this.disposeListeners.clear();
    this.viewStateListeners.clear();
    this.messageListeners.clear();
    this.unresponsiveListeners.clear();
    this.responsiveListeners.clear();
  }
}
