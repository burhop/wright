# /goal Prompt: LLM Onboarding And Provider Seed Files

```text
/goal Extend the Spec Kit-driven MCP Docker appliance so fresh Wright/Hermes
containers start successfully without a configured LLM, expose a browser-first
model-provider setup contract, and support reusable startup seed files for
repeatable Docker testing.

Use the existing specs/052-mcp-docker-appliance artifacts. Preserve the standard
Hermes + Wright Docker access pattern and do not corrupt host Wright/Hermes
state. Do not bake API keys, OAuth tokens, or model weights into Docker images.

Requirements:
1. Fresh containers with no LLM settings must start Wright and Hermes, report
   disconnected inference, and avoid writing a fake localhost LLM endpoint.
2. Existing LLM_API_URL, LLM_API_KEY, and LLM_API_MODEL env vars must keep
   working for OpenAI-compatible endpoints.
3. Add WRIGHT_LLM_CONFIG_FILE as a mounted YAML/JSON seed file for repeatable
   Docker tests.
4. Add startup options for WRIGHT_LLM_PROVIDER, WRIGHT_LLM_BASE_URL,
   WRIGHT_LLM_MODEL, WRIGHT_LLM_API_KEY, and WRIGHT_LLM_AUTH_FILE.
5. Support Codex/ChatGPT reuse through Hermes' openai-codex provider. A seed
   file can point at a mounted Hermes auth.json payload or inline a disposable
   access_token/refresh_token pair for local testing.
6. Expose setup API metadata for Codex, OpenAI-compatible endpoints, and Nous
   Portal, and provide a Wright browser page that wraps Hermes' Codex
   device-code login and OpenAI-compatible endpoint configuration.
7. Add docs and examples for engineers who are not software developers,
   including docker-mcp-run.sh and compose usage.
8. Add focused tests for the seed helper, Codex auth materialization, setup API
   provider metadata/configuration, and shell syntax.

Validate with focused pytest, py_compile, and bash -n. Update tasks.md evidence
with the results.
```
