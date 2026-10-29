# Actual bridge/backend readiness navigation

The compiled native UI, frozen bridge/backend source 99e97530 and installed candidate wheel 0eec3aaf69ff53bbee671532b27682c2ccf795ed91a04503d648eac919488813 now pass the read-only readiness correction journey. Browser host is simulated Linux; discovery and readiness responses come from real MCP/HTTP owners, not fixture responses.

Before the fix, Run workflow correctly reported the unconfigured CAD step, but Open affected step returned HTTP400: the desktop execution guard tried compiling unready source before allowing read-only navigation. The exact navigation endpoint now reaches its existing scope/source/block/run owners after desktop-session checks. Execution remains gated. 54 boundary tests pass, including unknown-session denial and unchanged run rejection.

The actual browser test confirms the reported CAD step opens, built-in Wright operations do not appear as installed engineering servers, the selector remains disabled with an honest missing-server message, and saved source remains identical with zero saves/runs. The screenshot records the 480px view. A direct Connections action in this unbound inspector message remains a usability gap.

Private reproduction: candidate-037/browser-readiness.mjs failed against c6e25ccc; browser-readiness-fixed.mjs passes against 99e97530. Retained logs and receipts are in .local-run/experience-review/candidate-037/. Service session 90411 runs only the fresh candidate on port18337; installed plugin and other services remain unchanged. Actual Windows, complete engineering execution, full gates and release are not established.
