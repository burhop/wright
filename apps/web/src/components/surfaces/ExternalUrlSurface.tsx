import { useState } from 'react'


export interface ExternalUrlApprovalView {
  approvalId: string
  normalizedUrl: string
  displayOrigin: string
  reason: string
  expiresAt: string
}

export interface ExternalUrlSurfaceProps {
  approval: ExternalUrlApprovalView
  openExternal: (absoluteUrl: string) => Promise<void>
}

export function ExternalUrlSurface({ approval, openExternal }: ExternalUrlSurfaceProps) {
  const [state, setState] = useState<'idle' | 'opening' | 'failed'>('idle')

  const open = async () => {
    setState('opening')
    try {
      await openExternal(approval.normalizedUrl)
      setState('idle')
    } catch {
      setState('failed')
    }
  }

  return (
    <section
      aria-labelledby={`external-url-${approval.approvalId}`}
      data-testid="surface-external-url"
    >
      <h2 id={`external-url-${approval.approvalId}`}>Open {approval.displayOrigin}</h2>
      <p>{approval.reason}</p>
      <p>
        This undeclared destination opens directly in your system browser. It is not
        sent through the Wright proxy and receives no Wright credentials, tool bridge,
        or managed lifecycle authority.
      </p>
      <p>
        Approval expires <time dateTime={approval.expiresAt}>{approval.expiresAt}</time>.
      </p>
      <button
        type="button"
        data-testid="surface-external-open"
        disabled={state === 'opening'}
        onClick={() => void open()}
      >
        {state === 'opening' ? 'Opening…' : 'Open in browser'}
      </button>
      {state === 'failed' && (
        <p role="alert">
          Wright could not ask the system browser to open this approved destination.
        </p>
      )}
    </section>
  )
}
