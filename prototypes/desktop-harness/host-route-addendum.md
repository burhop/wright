# Addendum to the preserved Windows handoff

The app reports the integration chat on the GB10 SSH execution host. Current
official docs make MCP configuration host-specific. The earlier implication
that GB10 paths cannot serve a Windows desktop was too broad: those paths can
be appropriate when the chat's MCP executor is GB10. Confirm the executor before
choosing a transport. See native-host-connection.md for the concrete simpler
proposal; Windows-local chats still need the prepared SSH-wrapper route.

Archive04 and its frozen target are unchanged. This addendum neither installs
a plugin nor authorizes live changes, target migration, desktop restart or a
new authentication path. Native GB10 registration still needs specific approval;
Windows browser routing and actual rendered Workflows remain unverified.
