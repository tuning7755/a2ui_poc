# Run

```bash
cd zhida
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

Notes:
- The app auto-loads env vars from `zhida/.env`.
- `.env` values do not override already-exported system env vars.

# LLM routing (LiteLLM + Qwen direct)

Supported modes:
- `LLM_MODE=litellm` (default): primary via LiteLLM gateway
- `LLM_MODE=qwen_direct`: primary direct to Qwen endpoint

Fallback:
- `LLM_FALLBACK_ENABLED=true` enables timeout fallback to the other provider.
- Example: with `LLM_MODE=litellm`, if timeout occurs, auto fallback to `qwen_direct`.

Qwen direct settings:
- `QWEN_MODEL=qwen-plus`
- `QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `QWEN_API_KEY=...` (or set `DASHSCOPE_API_KEY`)

# LangSmith (optional)

Set these in `.env` to enable tracing:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY=...`
- `LANGSMITH_PROJECT=a2ui-revenue-poc`
- `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`

# Test

```bash
curl -X POST "http://localhost:8080/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询月度收入走势"}'
```

```bash
curl -X POST "http://localhost:8080/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询月度订单量趋势"}'
```

```bash
curl -X POST "http://localhost:8080/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询不同价格带订单量分布"}'
```
