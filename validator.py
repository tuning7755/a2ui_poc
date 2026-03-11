from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)
REQUIRED_TOP_KEYS = ("beginRendering", "surfaceUpdate", "dataModelUpdate")


def validate_a2ui_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    for key in REQUIRED_TOP_KEYS:
        if key not in payload:
            return False, f"Missing top-level key: {key}"

    begin = payload.get("beginRendering", {})
    update = payload.get("surfaceUpdate", {})
    data_update = payload.get("dataModelUpdate", {})

    if not isinstance(update.get("components"), list) or not update.get("components"):
        return False, "surfaceUpdate.components must be a non-empty list"

    if not isinstance(data_update.get("contents"), list) or not data_update.get("contents"):
        return False, "dataModelUpdate.contents must be a non-empty list"

    sid1 = begin.get("surfaceId")
    sid2 = update.get("surfaceId")
    sid3 = data_update.get("surfaceId")
    if sid1 and sid2 and sid3 and len({sid1, sid2, sid3}) != 1:
        return False, "surfaceId must be consistent across beginRendering/surfaceUpdate/dataModelUpdate"

    logger.info("A2UI payload validation passed.")
    return True, ""
