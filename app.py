from __future__ import annotations

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent_service import RevenueUiAgentService
from schemas import GenerateUiRequest


log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2UI Revenue POC (LangChain + LiteLLM)")
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]
allow_all_origins = cors_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
service = RevenueUiAgentService()


@app.get("/health")
def health() -> dict[str, str]:
    logger.debug("Health check called")
    return {"status": "ok"}


@app.post("/api/ui/generate")
def generate_ui(req: GenerateUiRequest) -> dict:
    request_id = str(uuid.uuid4())
    logger.info("[%s] Incoming generate request. query=%s", request_id, req.query)
    try:
        result = service.generate_ui(req.query)
        result.setdefault("meta", {})["request_id"] = request_id
        logger.info("[%s] Generate request succeeded.", request_id)
        return result
    except Exception as exc:
        logger.exception("[%s] Generate request failed.", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "A2UI_GENERATION_FAILED",
                "message": "Failed to generate valid A2UI JSON",
                "details": str(exc),
                "request_id": request_id,
            },
        ) from exc
