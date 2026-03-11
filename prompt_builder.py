from __future__ import annotations

import logging
from pathlib import Path


logger = logging.getLogger(__name__)
LOCAL_DIR = Path(__file__).resolve().parent


def _read_text(path: Path, fallback: str = "{}") -> str:
    try:
        content = path.read_text(encoding="utf-8")
        logger.info("Loaded prompt asset: %s", path.name)
        return content
    except FileNotFoundError:
        logger.warning("Prompt asset not found: %s. Using fallback.", path)
        return fallback


def load_prompt_assets() -> dict[str, str]:
    return {
        "catalog": _read_text(LOCAL_DIR / "custom_catalog_definition.json"),
        "example": _read_text(LOCAL_DIR / "custom_example.json"),
    }


def build_ui_prompt(query: str, tool_data_json: str, assets: dict[str, str], agent_instruction: str) -> str:
    prompt = f"""
{agent_instruction}

--- WORKFLOW AND RULES ---
1. Analyze the user's BI intent.
2. Use ONLY the provided tool result data to populate UI data.
3. Reuse example structure and component patterns.
4. Return valid A2UI JSON object only.

--- BEGIN USER QUERY ---
{query}
--- END USER QUERY ---

--- BEGIN QUERY RESULT JSON ---
{tool_data_json}
--- END QUERY RESULT JSON ---

--- BEGIN A2UI EXAMPLE ---
{assets['example']}
--- END A2UI EXAMPLE ---

--- BEGIN A2UI CATALOG ---
{assets['catalog']}
--- END A2UI CATALOG ---
""".strip()
    logger.info("Built prompt for query. length=%s chars", len(prompt))
    return prompt
