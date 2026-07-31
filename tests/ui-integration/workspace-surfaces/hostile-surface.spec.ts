import fs from 'node:fs'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { liveSurface, mockWorkspaceShell } from './presentation-fixture'


const fixtureRoot = path.resolve(
  process.cwd(), 'tests/fixtures/workspace_surfaces/hostile_surface',
)
const hostileHtml = fs.readFileSync(path.join(fixtureRoot, 'index.html'), 'utf8')

test.describe('hostile surface security boundary', () => {
  test('blocks cross-origin, credential, API, popup, device and download attempts', async ({
    page,
    context,
  }) => {
    const surface = {
      ...liveSurface('ready', { sharing: 'isolated' }),
      title: 'Hostile conformance app',
      source: {
        kind: 'live_app',
        sourceId: 'wright-hostile-conformance',
        sourceVersion: '1.0.0',
        manifestId: 'wright-hostile-conformance',
      },
    }
    await mockWorkspaceShell(page, [surface])
    await context.addCookies([
      { name: 'wright_control', value: 'must-not-leak', url: 'http://localhost:5173' },
    ])
    await page.addInitScript(() => {
      localStorage.setItem('wright.control.secret', 'must-not-leak')
    })
    await page.route('**/api/workspace/surfaces/surface-app/presentations', (route) =>
      route.fulfill({
        status: 201,
        json: {
          presentationId: 'hostile',
          instanceId: 'instance-hostile',
          generation: 3,
          kind: 'panel',
          absoluteBootstrapUrl:
            'http://s-hostile.localhost:5173/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345',
          expiresAt: '2026-07-30T12:01:00Z',
        },
      }),
    )
    await page.route('http://s-hostile.localhost:5173/**', (route) => {
      if (new URL(route.request().url()).pathname.startsWith('/api')) {
        return route.fulfill({ status: 404, body: 'not found' })
      }
      return route.fulfill({
        contentType: 'text/html',
        headers: {
          'Content-Security-Policy':
            "default-src 'self'; script-src 'unsafe-inline'; object-src 'none'; base-uri 'none'",
          'Referrer-Policy': 'no-referrer',
        },
        body: hostileHtml,
      })
    })

    const popups: unknown[] = []
    context.on('page', (popup) => popups.push(popup))
    await page.goto('/workspace/ws-1')
    await page.getByTestId('surface-open-panel').click()

    const iframe = page.locator('iframe[title="Hostile conformance app"]')
    await expect(iframe).toBeVisible()
    await expect(iframe).toHaveAttribute('sandbox', 'allow-scripts allow-forms allow-same-origin')
    await expect(iframe).toHaveAttribute('referrerpolicy', 'no-referrer')
    await expect(iframe).toHaveAttribute('allow', /camera 'none'/)
    await expect(iframe).toHaveAttribute('allow', /microphone 'none'/)
    await expect(iframe).toHaveAttribute('allow', /geolocation 'none'/)
    const sandbox = (await iframe.getAttribute('sandbox'))?.split(/\s+/) ?? []
    expect(sandbox).not.toContain('allow-popups')
    expect(sandbox).not.toContain('allow-downloads')
    expect(sandbox).not.toContain('allow-top-navigation')

    const frame = page.frameLocator('iframe[title="Hostile conformance app"]')
    for (const [id, outcome] of [
      ['parent-document', 'blocked'],
      ['parent-storage', 'blocked'],
      ['control-cookie', 'isolated'],
      ['popup', 'blocked'],
      ['control-api', 'blocked'],
      ['camera', 'blocked'],
      ['download', 'attempted-but-sandboxed'],
      ['wildcard-message', 'sent-without-authority'],
    ] as const) {
      await expect(frame.locator(`#${id}`)).toHaveText(outcome)
    }
    expect(popups).toHaveLength(0)
    await expect(page).toHaveURL(/\/workspace\/ws-1$/)
    expect(await page.evaluate(() => localStorage.getItem('wright.control.secret'))).toBe(
      'must-not-leak',
    )
  })

  test('fixture audit expectations are stable and contain no sensitive values', () => {
    const audit = JSON.parse(
      fs.readFileSync(path.join(fixtureRoot, 'expected-audit.json'), 'utf8'),
    ) as {
      expectedOutcomes: { code: string; allowed: boolean }[]
      forbiddenAuditFields: string[]
    }
    expect(audit.expectedOutcomes).toHaveLength(9)
    expect(audit.expectedOutcomes.every((item) => !item.allowed)).toBe(true)
    expect(audit.expectedOutcomes.every((item) => /^SURFACE_[A-Z0-9_]+$/.test(item.code))).toBe(true)
    expect(audit.forbiddenAuditFields).toEqual([
      'authorization', 'cookie', 'query', 'target_pin', 'user_content', 'upstream_logs',
    ])
    const serialized = JSON.stringify(audit)
    expect(serialized).not.toContain('must-not-leak')
    expect(serialized).not.toContain('Bearer ')
  })
})
