# A2UI POC

Minimal backend POC for generating A2UI JSON from:
- a natural-language query
- mock BI data returned by a LangChain tool
- local `catalog` and `example` files

## Features

- LangChain-based agent flow with explicit tool-first execution
- LiteLLM and direct Qwen access, with timeout fallback
- Local `custom_catalog_definition.json` and `custom_example.json`
- FastAPI endpoint with CORS enabled
- LangSmith tracing and structured backend logs
- Docker and `docker compose` support

## Local Run

```bash
cd zhida
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app:app --host 0.0.0.0 --port 8089 --reload
```

Notes:
- The app auto-loads env vars from `zhida/.env`.
- `.env` values do not override already-exported system env vars.

## Docker Run

Build and run with Docker:

```bash
cd zhida
docker build -t a2ui-zhida .
docker run --rm -p 8089:8089 --env-file .env a2ui-zhida uvicorn app:app --host 0.0.0.0 --port 8089
```

Run with Compose:

```bash
cd zhida
docker compose up --build
```

The compose file uses this pre-created external network:

```bash
docker network create --driver bridge --subnet 172.10.0.0/16 --gateway 172.10.0.1 a2ui-zhida_default
```

## Configuration

### LLM Routing

Supported modes:
- `LLM_MODE=litellm`: primary via LiteLLM gateway
- `LLM_MODE=qwen_direct`: primary direct to Qwen endpoint

Fallback:
- `LLM_FALLBACK_ENABLED=true` enables timeout fallback to the other provider

Qwen direct settings:
- `QWEN_MODEL=qwen-plus`
- `QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `QWEN_API_KEY=...` or `DASHSCOPE_API_KEY=...`

### LangSmith

Set these in `.env` to enable tracing:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY=...`
- `LANGSMITH_PROJECT=a2ui-revenue-poc`
- `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`

### CORS

Default behavior:
- `CORS_ALLOW_ORIGINS=*` allows all origins
- wildcard mode uses `allow_credentials=False`

Example for specific frontend origins:

```env
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:5173
```

## API

Health check:

```bash
curl http://localhost:8089/health
```

Generate UI:

```bash
curl -X POST "http://localhost:8089/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询月度收入走势"}'
```

```bash
curl -X POST "http://localhost:8089/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询月度订单量趋势"}'
```

```bash
curl -X POST "http://localhost:8089/api/ui/generate" \
  -H "Content-Type: application/json" \
  -d '{"query":"查询不同价格带订单量分布"}'
```

## Supported Queries

- `查询月度收入走势`
- `查询月度订单量趋势`
- `查询不同价格带订单量分布`
