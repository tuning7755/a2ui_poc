from __future__ import annotations

import json
import logging
import re
from typing import Any


logger = logging.getLogger(__name__)
_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_text(raw_text: str) -> str:
    match = _JSON_BLOCK_RE.search(raw_text)
    if match:
        logger.info("Detected markdown json fence in model output; extracting payload.")
        return match.group(1).strip()
    return raw_text.strip()


def parse_json_object(raw_text: str) -> dict[str, Any]:
    text = extract_json_text(raw_text)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("A2UI payload must be a JSON object.")
    logger.info("Parsed model output into JSON object successfully.")
    return payload
