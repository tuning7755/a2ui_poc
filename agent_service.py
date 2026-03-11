from __future__ import annotations

import json
import logging
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent_instruction import AGENT_INSTRUCTION
from llm_factory import create_llm_bundle
from parser import parse_json_object
from prompt_builder import build_ui_prompt, load_prompt_assets
from tools import get_revenue_trend
from validator import validate_a2ui_payload

logger = logging.getLogger(__name__)

try:
    from langsmith import traceable
except Exception:  # pragma: no cover
    def traceable(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator


def _is_timeout_error(exc: Exception) -> bool:
    text = str(exc).lower()
    timeout_tokens = (
        "timeout",
        "timed out",
        "request timed out",
        "read timeout",
        "connect timeout",
        "504",
    )
    return any(token in text for token in timeout_tokens) or isinstance(exc, TimeoutError)


class RevenueUiAgentService:
    def __init__(self) -> None:
        bundle = create_llm_bundle()
        self._llm = bundle["primary"]
        self._llm_name = bundle["primary_name"]
        self._fallback_llm = bundle["fallback"]
        self._fallback_llm_name = bundle["fallback_name"]
        self._assets = load_prompt_assets()
        self._langsmith_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        logger.info(
            "RevenueUiAgentService initialized. langsmith_enabled=%s primary_llm=%s fallback_llm=%s",
            self._langsmith_enabled,
            self._llm_name,
            self._fallback_llm_name,
        )

    @traceable(name="invoke_ui_model", run_type="llm")
    def _invoke_model_with_llm(self, llm: Any, llm_name: str, prompt: str) -> str:
        logger.info("Invoking LLM provider=%s prompt_length=%s", llm_name, len(prompt))
        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the final A2UI JSON now."),
        ])
        content = response.content if isinstance(response.content, str) else json.dumps(response.content, ensure_ascii=False)
        logger.info("LLM invocation completed provider=%s output_length=%s", llm_name, len(content))
        return content

    def _invoke_model(self, prompt: str) -> tuple[str, str]:
        try:
            output = self._invoke_model_with_llm(self._llm, self._llm_name, prompt)
            return output, self._llm_name
        except Exception as exc:
            if self._fallback_llm is not None and _is_timeout_error(exc):
                logger.warning(
                    "Primary LLM provider=%s timed out. Falling back to provider=%s. error=%s",
                    self._llm_name,
                    self._fallback_llm_name,
                    exc,
                )
                output = self._invoke_model_with_llm(
                    self._fallback_llm, self._fallback_llm_name or "fallback", prompt
                )
                return output, self._fallback_llm_name or "fallback"
            raise

    @traceable(name="generate_revenue_ui", run_type="chain")
    def generate_ui(self, query: str) -> dict[str, Any]:
        logger.info("Generate UI request started. query=%s", query)

        tool_data = get_revenue_trend.invoke({"query": query})
        tool_data_json = json.dumps(tool_data, ensure_ascii=False)
        logger.info("Tool data prepared. keys=%s", list(tool_data.keys()))

        prompt = build_ui_prompt(
            query=query,
            tool_data_json=tool_data_json,
            assets=self._assets,
            agent_instruction=AGENT_INSTRUCTION,
        )

        retry_count = 0
        raw_output, model_provider = self._invoke_model(prompt)

        try:
            payload = parse_json_object(raw_output)
            valid, err = validate_a2ui_payload(payload)
            if not valid:
                raise ValueError(err)
        except Exception as first_error:
            logger.warning("First-pass validation failed. retrying once. error=%s", first_error)
            retry_count = 1
            repair_prompt = (
                prompt
                + "\n\nYour previous output was invalid."
                + f" Error: {first_error}."
                + " Return ONLY a valid A2UI JSON object with required top-level keys."
            )
            raw_output, model_provider = self._invoke_model(repair_prompt)
            payload = parse_json_object(raw_output)
            valid, err = validate_a2ui_payload(payload)
            if not valid:
                logger.error("Second-pass validation failed. error=%s", err)
                raise ValueError(err)

        logger.info("Generate UI request completed successfully. retry_count=%s", retry_count)
        return {
            "query": query,
            "tool_data": tool_data,
            "a2ui": payload,
            "meta": {
                "tool_called": True,
                "retry_count": retry_count,
                "langsmith_enabled": self._langsmith_enabled,
                "model_provider": model_provider,
                "fallback_configured": self._fallback_llm is not None,
            },
        }
