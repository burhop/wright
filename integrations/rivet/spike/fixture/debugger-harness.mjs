import WebSocket from "ws";
import { startDebuggerServer } from "@ironclad/rivet-node";
import { writeEvidence } from "../scripts/evidence.mjs";

const debuggerServer = startDebuggerServer({ host: "127.0.0.1", port: 0, allowGraphUpload: false });
await new Promise((resolvePromise, reject) => {
  debuggerServer.webSocketServer.once("listening", resolvePromise);
  debuggerServer.webSocketServer.once("error", reject);
});
const address = debuggerServer.webSocketServer.address();
if (!address || typeof address === "string") throw new Error("Debugger did not bind a local port.");
const endpoint = `ws://127.0.0.1:${address.port}`;
const events = [];
try {
  await new Promise((resolvePromise, reject) => {
    const socket = new WebSocket(endpoint);
    socket.once("open", () => { events.push({ kind: "unauthenticated-connect" }); socket.close(); resolvePromise(); });
    socket.once("error", reject);
  });
  const { target } = await writeEvidence("runner", "passed", {
    debuggerEndpoint: "redacted-local-generated",
    unauthenticatedConnectionAccepted: true,
    disposition: "adapter-required: Wright must wrap/debugger-bind a generation-scoped authenticated channel"
  }, events, "debugger");
  console.log(target);
} finally {
  await new Promise((resolvePromise) => debuggerServer.webSocketServer.close(resolvePromise));
}
