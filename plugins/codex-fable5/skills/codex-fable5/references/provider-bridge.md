# Provider Bridge

Use this reference only when the user wants Codex to route model calls to an actual Fable-compatible Anthropic model. A skill cannot create access to a model, and this repository does not provide model access. The user must have model availability, credentials, and a gateway that Codex can call.

Verified on 2026-07-08 against the current local `codex-cli 0.128.0`, the official Codex manual, LiteLLM docs, and Anthropic/Claude Platform docs.

## Reality Check

- Prompt instructions can emulate parts of a Fable-style workflow, but they cannot reproduce a model's weights, context window, training data, latency, or hidden safety systems.
- Codex custom providers are configured with `model_provider` and `[model_providers.<id>]` in `config.toml`. The official Codex manual documents `base_url`, `env_key`, optional command-backed auth, and `wire_api = "responses"` for OpenAI-compatible proxy providers.
- Codex can point at providers that support Chat Completions or Responses APIs, but the Codex manual says Chat Completions support is deprecated and will be removed in a future Codex release. Prefer a Responses-compatible path for new provider bridge work.
- Anthropic's native API is the Claude Messages API. Anthropic also documents an OpenAI SDK compatibility layer, but says it is primarily for testing/comparison and not the preferred long-term production path for most use cases.
- LiteLLM documents an OpenAI-compatible proxy, the `anthropic/` provider route, and a `/responses` to `/chat/completions` bridge for calling non-Responses models such as Anthropic.
- Model availability changes. Verify the current Anthropic model docs and your own account access before changing Codex config. Keep examples placeholder-based unless access is proven in the user's environment.

## Recommended Gateway

Use LiteLLM Proxy when you need a practical OpenAI-compatible gateway for Anthropic models. LiteLLM documents OpenAI-compatible proxy support, Anthropic provider support, and Responses API support.

Typical flow:

```bash
python3 -m pip install "litellm[proxy]"
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
litellm --config litellm-fable5.yaml --host 127.0.0.1 --port 4000
```

Generate a starter LiteLLM config:

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/make_litellm_config.py \
  --model replace-with-current-anthropic-model \
  --alias your-codex-model-alias \
  --output litellm-fable5.yaml
```

This generator prefixes Anthropic model names with `anthropic/` for LiteLLM routing, preserves an existing `anthropic/` prefix, quotes YAML strings, and uses `os.environ/ANTHROPIC_API_KEY` rather than embedding a secret.

## Codex Config Example

Put provider config in your user-level `~/.codex/config.toml`, not in a project-local config, when it changes authentication or model routing.

```toml
model_provider = "litellm-fable5"
model = "your-codex-model-alias"

[model_providers.litellm-fable5]
name = "LiteLLM Fable 5"
base_url = "http://127.0.0.1:4000/v1"
env_key = "LITELLM_API_KEY"
env_key_instructions = "Set LITELLM_API_KEY to the LiteLLM virtual key or any accepted proxy key."
wire_api = "responses"
```

If your LiteLLM proxy does not require virtual keys, set `LITELLM_API_KEY` to a placeholder value accepted by the proxy, or configure LiteLLM authentication properly and use the real virtual key.

## Validation Steps

1. Start the gateway.
2. Verify the gateway accepts an OpenAI Responses-style request for your configured alias:

```bash
curl http://127.0.0.1:4000/v1/responses \
  -H "Authorization: Bearer ${LITELLM_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"your-codex-model-alias","input":"ping","max_output_tokens":16}'
```

3. Start a new Codex session with the provider config.
4. Ask Codex to summarize its active model/provider only if the provider exposes that information. Do not treat a style change as proof of provider routing.
5. Run a small tool-using task, such as reading one file and editing one line, before attempting large autonomous work.

## Failure Modes

- No Anthropic access: use Fable-style Codex mode instead.
- Model retired or suspended: choose an available Anthropic model or return to OpenAI Codex models.
- Tool calling mismatch: update LiteLLM, enable parameter modification if needed, or use the native Codex model for tool-heavy coding work.
- Long-context mismatch: do not assume Anthropic's advertised context limits are usable through every gateway or Codex surface.
- Safety/refusal mismatch: provider-side refusals still apply and may differ from Codex/OpenAI refusals.

## Official Sources To Recheck

- Codex custom provider configuration: `https://developers.openai.com/codex/config-advanced#custom-model-providers`
- Codex model provider authentication: `https://developers.openai.com/codex/authentication#alternative-model-providers`
- LiteLLM Responses API bridge: `https://docs.litellm.ai/docs/response_api`
- LiteLLM Anthropic provider route: `https://docs.litellm.ai/docs/providers/anthropic`
- Anthropic model IDs and availability: `https://platform.claude.com/docs/en/about-claude/models/overview`
- Anthropic Models API list endpoint: `https://platform.claude.com/docs/en/api/models/list`
- Anthropic OpenAI SDK compatibility limitations: `https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk`
