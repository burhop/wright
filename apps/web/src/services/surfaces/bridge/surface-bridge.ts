export interface SurfaceBridgeBinding {
  workspaceId: string
  sessionId: string
  surfaceId: string
  instanceId: string
  presentationId: string
  generation: number
  documentOrigin: string
  serverId?: string
}

export type SurfaceBridgeMessageKind = 'request' | 'result' | 'error' | 'event' | 'cancel'

export interface SurfaceBridgeEnvelope {
  protocolVersion: '1.0'
  kind: SurfaceBridgeMessageKind
  messageId: string
  correlationId: string
  binding: SurfaceBridgeBinding
  operation: string
  sequence: number
  createdAt: string
  deadlineAt: string
  replyTo?: string
  payload?: unknown
}

interface MessageHost {
  addEventListener(type: 'message', listener: (event: MessageEvent) => void): void
  removeEventListener(type: 'message', listener: (event: MessageEvent) => void): void
}

interface MessageTarget {
  postMessage(message: unknown, targetOrigin: string): void
}

export interface SurfaceBridgeOptions {
  hostWindow: MessageHost
  targetWindow: MessageTarget
  targetOrigin: string
  binding: SurfaceBridgeBinding
  onMessage: (message: SurfaceBridgeEnvelope) => void
  onSecurityEvent?: (code: string) => void
  maximumMessageBytes?: number
  idFactory?: () => string
  now?: () => Date
  deadlineMilliseconds?: number
}

const kinds = new Set<SurfaceBridgeMessageKind>([
  'request', 'result', 'error', 'event', 'cancel',
])
const operationPattern = /^[a-z][a-z0-9_.:/-]{1,127}$/

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isBinding(value: unknown): value is SurfaceBridgeBinding {
  if (!isRecord(value)) return false
  const strings = [
    'workspaceId', 'sessionId', 'surfaceId', 'instanceId',
    'presentationId', 'documentOrigin',
  ]
  return strings.every((key) => typeof value[key] === 'string' && value[key] !== '')
    && Number.isInteger(value.generation) && Number(value.generation) >= 1
    && (value.serverId === undefined || typeof value.serverId === 'string')
}

function isEnvelope(value: unknown): value is SurfaceBridgeEnvelope {
  if (!isRecord(value) || value.protocolVersion !== '1.0') return false
  return kinds.has(value.kind as SurfaceBridgeMessageKind)
    && typeof value.messageId === 'string'
    && typeof value.correlationId === 'string'
    && isBinding(value.binding)
    && typeof value.operation === 'string'
    && operationPattern.test(value.operation)
    && Number.isInteger(value.sequence) && Number(value.sequence) >= 0
    && typeof value.createdAt === 'string' && !Number.isNaN(Date.parse(value.createdAt))
    && typeof value.deadlineAt === 'string' && !Number.isNaN(Date.parse(value.deadlineAt))
    && (value.replyTo === undefined || typeof value.replyTo === 'string')
}

function sameBinding(left: SurfaceBridgeBinding, right: SurfaceBridgeBinding): boolean {
  return left.workspaceId === right.workspaceId
    && left.sessionId === right.sessionId
    && left.surfaceId === right.surfaceId
    && left.instanceId === right.instanceId
    && left.presentationId === right.presentationId
    && left.documentOrigin === right.documentOrigin
    && left.serverId === right.serverId
}

export class SurfaceBridge {
  private readonly options: Required<Pick<SurfaceBridgeOptions,
    'maximumMessageBytes' | 'idFactory' | 'now' | 'deadlineMilliseconds' | 'onSecurityEvent'>>
    & Omit<SurfaceBridgeOptions,
      'maximumMessageBytes' | 'idFactory' | 'now' | 'deadlineMilliseconds' | 'onSecurityEvent'>
  private started = false
  private disposed = false
  private sequence = 0
  private readonly listener = (event: MessageEvent) => this.receive(event)

  constructor(options: SurfaceBridgeOptions) {
    let parsed: URL
    try {
      parsed = new URL(options.targetOrigin)
    } catch {
      throw new Error('Surface bridge requires an exact target origin')
    }
    if (options.targetOrigin === '*'
      || !['http:', 'https:'].includes(parsed.protocol)
      || parsed.origin !== options.targetOrigin
      || parsed.username !== '' || parsed.password !== ''
      || options.binding.documentOrigin !== options.targetOrigin) {
      throw new Error('Surface bridge requires an exact target origin')
    }
    const maximumMessageBytes = options.maximumMessageBytes ?? 4 * 1024 * 1024
    const deadlineMilliseconds = options.deadlineMilliseconds ?? 30_000
    if (maximumMessageBytes < 1 || deadlineMilliseconds < 1) {
      throw new Error('Surface bridge bounds must be positive')
    }
    this.options = {
      ...options,
      maximumMessageBytes,
      deadlineMilliseconds,
      idFactory: options.idFactory ?? (() => crypto.randomUUID()),
      now: options.now ?? (() => new Date()),
      onSecurityEvent: options.onSecurityEvent ?? (() => undefined),
    }
  }

  start(): void {
    if (this.disposed) throw new Error('Surface bridge is disposed')
    if (this.started) return
    this.started = true
    this.options.hostWindow.addEventListener('message', this.listener)
  }

  private reject(code: string): void {
    this.options.onSecurityEvent(code)
  }

  private receive(event: MessageEvent): void {
    if (this.disposed || !this.started) return
    if (event.origin !== this.options.targetOrigin) {
      this.reject('SURFACE_BRIDGE_ORIGIN_MISMATCH')
      return
    }
    if (event.source !== this.options.targetWindow) {
      this.reject('SURFACE_BRIDGE_SOURCE_MISMATCH')
      return
    }
    let encoded: string
    try {
      encoded = JSON.stringify(event.data)
    } catch {
      this.reject('SURFACE_BRIDGE_INVALID_MESSAGE')
      return
    }
    if (new TextEncoder().encode(encoded).byteLength > this.options.maximumMessageBytes) {
      this.reject('SURFACE_BRIDGE_MESSAGE_TOO_LARGE')
      return
    }
    if (!isEnvelope(event.data)) {
      this.reject('SURFACE_BRIDGE_INVALID_MESSAGE')
      return
    }
    if (event.data.binding.generation !== this.options.binding.generation) {
      this.reject('SURFACE_BRIDGE_STALE_GENERATION')
      return
    }
    if (!sameBinding(event.data.binding, this.options.binding)) {
      this.reject('SURFACE_BRIDGE_BINDING_MISMATCH')
      return
    }
    this.options.onMessage(event.data)
  }

  send(kind: SurfaceBridgeMessageKind, operation: string, payload?: unknown): SurfaceBridgeEnvelope {
    if (this.disposed) throw new Error('Surface bridge is disposed')
    if (!operationPattern.test(operation)) throw new Error('Surface bridge operation is invalid')
    const now = this.options.now()
    const messageId = this.options.idFactory()
    const message: SurfaceBridgeEnvelope = {
      protocolVersion: '1.0',
      kind,
      messageId,
      correlationId: messageId,
      binding: { ...this.options.binding },
      operation,
      sequence: this.sequence++,
      createdAt: now.toISOString(),
      deadlineAt: new Date(now.getTime() + this.options.deadlineMilliseconds).toISOString(),
      payload,
    }
    const encoded = JSON.stringify(message)
    if (new TextEncoder().encode(encoded).byteLength > this.options.maximumMessageBytes) {
      throw new Error('Surface bridge message exceeds the configured limit')
    }
    this.options.targetWindow.postMessage(message, this.options.targetOrigin)
    return message
  }

  dispose(): void {
    if (this.disposed) return
    this.disposed = true
    if (this.started) {
      this.options.hostWindow.removeEventListener('message', this.listener)
      this.started = false
    }
  }
}
