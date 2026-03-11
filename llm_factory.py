from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TypedDict

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


class LlmBundle(TypedDict):
    primary: ChatOpenAI
    primary_name: str
    fallback: ChatOpenAI | None
    fallback_name: str | None


def _load_env_file() -> None:
    env_path = Path(__file__).with_name(".env")
    if load_dotenv is None:
        logger.warning("python-dotenv is not installed; .env file will not be loaded automatically.")
        return
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logger.info("Loaded environment variables from %s", env_path)
    else:
        logger.info("No .env file found at %s; using process environment only.", env_path)


def _new_chat_openai(
    *,
    model: str,
    base_url: str,
    api_key: str,
    temperature: float,
    timeout: float,
    tag: str,
) -> ChatOpenAI:
    logger.info(
        "Initializing %s ChatOpenAI model=%s base_url=%s temperature=%s timeout=%s",
        tag,
        model,
        base_url,
        temperature,
        timeout,
    )
    if not api_key:
        logger.warning("%s api_key is empty.", tag)
    if api_key == "dummy":
        logger.warning("%s api_key=dummy. Ensure upstream accepts this.", tag)

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
    )


def _create_litellm_llm() -> ChatOpenAI:
    model = os.getenv("LITELLM_MODEL", "openai/qwen-plus")
    base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    api_key = os.getenv("LITELLM_API_KEY", "dummy")
    temperature = float(os.getenv("LITELLM_TEMPERATURE", "0.1"))
    timeout = float(os.getenv("LITELLM_TIMEOUT", "60"))

    return _new_chat_openai(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
        tag="LiteLLM",
    )


def _create_qwen_direct_llm() -> ChatOpenAI:
    model = os.getenv("QWEN_MODEL", "qwen-plus")
    base_url = os.getenv(
        "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
    temperature = float(os.getenv("QWEN_TEMPERATURE", "0.1"))
    timeout = float(os.getenv("QWEN_TIMEOUT", "60"))

    return _new_chat_openai(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
        tag="QwenDirect",
    )


def create_llm_bundle() -> LlmBundle:
    _load_env_file()

    mode = os.getenv("LLM_MODE", "litellm").strip().lower()
    fallback_enabled = os.getenv("LLM_FALLBACK_ENABLED", "true").strip().lower() == "true"

    if mode == "qwen_direct":
        primary = _create_qwen_direct_llm()
        primary_name = "qwen_direct"
        fallback = _create_litellm_llm() if fallback_enabled else None
        fallback_name = "litellm" if fallback is not None else None
    else:
        primary = _create_litellm_llm()
        primary_name = "litellm"
        fallback = _create_qwen_direct_llm() if fallback_enabled else None
        fallback_name = "qwen_direct" if fallback is not None else None

    logger.info(
        "LLM routing configured. mode=%s primary=%s fallback=%s",
        mode,
        primary_name,
        fallback_name,
    )

    return {
        "primary": primary,
        "primary_name": primary_name,
        "fallback": fallback,
        "fallback_name": fallback_name,
    }
