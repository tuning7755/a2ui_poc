from __future__ import annotations

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_revenue_trend(query: str) -> dict:
    """Get mock monthly metric trend data by natural-language query."""
    logger.info("Tool get_revenue_trend called. query=%s", query)

    months = [
        "1月", "2月", "3月", "4月", "5月", "6月",
        "7月", "8月", "9月", "10月", "11月", "12月",
    ]
    normalized_query = query.lower()

    if "价格带" in query or "price" in normalized_query or "band" in normalized_query:
        default = {
            "page_title": "2025 销售分析",
            "card_title": "价格带订单量分布",
            "unit": "单",
            "metric": "orders_by_price_band",
            "metric_label": "订单量",
            "actual_label": "订单量",
            "bands": ["0-50元", "50-100元", "100-150元", "150-200元", "200-300元", "300元以上"],
            "actual": [420, 680, 910, 760, 430, 180],
            "query": query,
        }
    elif "订单" in query or "order" in normalized_query:
        default = {
            "page_title": "2025 经营核心指标",
            "card_title": "月度订单量趋势（Actual vs Budget）",
            "unit": "单",
            "metric": "order_count",
            "metric_label": "订单量",
            "actual_label": "实际订单量",
            "budget_label": "预算订单量",
            "months": months,
            "actual": [820, 860, 910, 960, 1020, 1080, 1110, 1150, 1210, 1280, 1340, 1420],
            "budget": [800, 840, 880, 930, 980, 1030, 1070, 1110, 1170, 1230, 1290, 1360],
            "query": query,
        }
    else:
        default = {
            "page_title": "2025 财务核心指标",
            "card_title": "月度营业收入走势（Actual vs Budget）",
            "unit": "万元",
            "metric": "revenue",
            "metric_label": "营业收入",
            "actual_label": "实际收入",
            "budget_label": "预算收入",
            "months": months,
            "actual": [120, 128, 135, 149, 158, 166, 174, 182, 191, 203, 214, 226],
            "budget": [110, 120, 130, 140, 150, 160, 168, 176, 185, 195, 205, 220],
            "query": query,
        }

    logger.info(
        "Tool get_revenue_trend returning metric=%s points=%s axis_items=%s",
        default["metric"],
        len(default["actual"]),
        len(default.get("months", default.get("bands", []))),
    )
    return default
