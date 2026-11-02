// Keep the bundled viewer's object identifiers on Web Crypto without changing
// global Math or maintaining a modified copy of the third-party renderer.
export function secureViewerRandom() {
  if (!globalThis.crypto?.getRandomValues)
    throw new Error("Secure random values are unavailable for the 3D preview.");
  const values = new Uint32Array(1);
  globalThis.crypto.getRandomValues(values);
  return values[0] / 4294967296;
}
