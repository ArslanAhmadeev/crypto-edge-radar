"""Small, transparent helpers for the TGE Polymarket pilot backtest."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

import pandas as pd


_THRESHOLD_RE = re.compile(
    r">\s*\$?\s*(?P<threshold>[0-9]+(?:\.[0-9]+)?)\s*"
    r"(?P<unit>[KMBT]?)\s+(?P<probability>[0-9]+(?:\.[0-9]+)?)\s*%",
    re.IGNORECASE,
)
_UNIT_MULTIPLIERS = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def _is_missing(value: Any) -> bool:
    """Return True for None, NaN and pandas missing values."""

    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def calculate_roi(sale_price: float | None, outcome_price: float | None) -> float:
    """Calculate percentage-point ROI, returning NaN when an input is missing."""

    if _is_missing(sale_price) or _is_missing(outcome_price):
        return math.nan
    sale_price = float(sale_price)
    outcome_price = float(outcome_price)
    if sale_price <= 0:
        raise ValueError("sale_price must be positive")
    return (outcome_price / sale_price - 1.0) * 100.0


def calculate_fdv(price: float | None, total_supply: float | None) -> float:
    """Calculate fully diluted valuation, returning NaN when an input is missing."""

    if _is_missing(price) or _is_missing(total_supply):
        return math.nan
    price = float(price)
    total_supply = float(total_supply)
    if price < 0:
        raise ValueError("price cannot be negative")
    if total_supply <= 0:
        raise ValueError("total_supply must be positive")
    return price * total_supply


def filter_actionable(frame: pd.DataFrame) -> pd.DataFrame:
    """Return only rows whose Polymarket signal existed before sale close."""

    if "pm_actionability" not in frame.columns:
        raise KeyError("pm_actionability column is required")
    return frame.loc[frame["pm_actionability"].eq("actionable")].copy()


def select_day1_outcome(
    row: Mapping[str, Any], *, allow_proxy: bool = False
) -> dict[str, Any]:
    """Select a day-1 outcome without silently substituting a proxy.

    Exact daily-close fields always take priority. Proxy fields are returned only
    when ``allow_proxy`` is explicitly enabled.
    """

    exact_price = row.get("price_1d_usd")
    if not _is_missing(exact_price):
        return {
            "price_usd": float(exact_price),
            "roi_pct": calculate_roi(row.get("sale_price_usd"), exact_price),
            "fdv_usd": calculate_fdv(exact_price, row.get("total_supply")),
            "quality": "exact",
            "method": "daily close",
        }

    proxy_price = row.get("price_1d_proxy_usd")
    if allow_proxy and not _is_missing(proxy_price):
        return {
            "price_usd": float(proxy_price),
            "roi_pct": calculate_roi(row.get("sale_price_usd"), proxy_price),
            "fdv_usd": calculate_fdv(proxy_price, row.get("total_supply")),
            "quality": "proxy",
            "method": row.get("price_1d_proxy_method"),
        }

    return {
        "price_usd": math.nan,
        "roi_pct": math.nan,
        "fdv_usd": math.nan,
        "quality": "missing",
        "method": None,
    }


def parse_pm_thresholds(value: Any) -> list[dict[str, float]]:
    """Parse strings such as ``>$50M 91%; >$100M 65%`` into thresholds."""

    if _is_missing(value):
        return []
    thresholds: list[dict[str, float]] = []
    for match in _THRESHOLD_RE.finditer(str(value)):
        unit = match.group("unit").upper()
        threshold = float(match.group("threshold")) * _UNIT_MULTIPLIERS[unit]
        probability = float(match.group("probability")) / 100.0
        thresholds.append(
            {"threshold_usd": threshold, "probability": probability}
        )
    return sorted(thresholds, key=lambda item: item["threshold_usd"])


def proxy_median_floor(
    thresholds: list[dict[str, float]], *, probability_cutoff: float = 0.5
) -> float:
    """Return the highest threshold with probability at least the cutoff.

    This is a lower-bound summary of a threshold market, not an expected FDV.
    """

    eligible = [
        item["threshold_usd"]
        for item in thresholds
        if item["probability"] >= probability_cutoff
    ]
    return max(eligible, default=math.nan)


def build_analysis_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Add derived outcomes and explicitly labeled signal-quality fields."""

    frame = raw.copy()

    for horizon in (1, 7, 30, 90):
        price_column = f"price_{horizon}d_usd"
        frame[f"derived_roi_{horizon}d_pct"] = frame.apply(
            lambda row: calculate_roi(row["sale_price_usd"], row[price_column]),
            axis=1,
        )
        frame[f"derived_fdv_{horizon}d_usd"] = frame.apply(
            lambda row: calculate_fdv(row[price_column], row["total_supply"]),
            axis=1,
        )

    exact_day1 = frame.apply(
        lambda row: pd.Series(select_day1_outcome(row, allow_proxy=False)), axis=1
    )
    sensitivity_day1 = frame.apply(
        lambda row: pd.Series(select_day1_outcome(row, allow_proxy=True)), axis=1
    )
    frame["day1_exact_roi_pct"] = exact_day1["roi_pct"]
    frame["day1_exact_fdv_usd"] = exact_day1["fdv_usd"]
    frame["day1_sensitivity_roi_pct"] = sensitivity_day1["roi_pct"]
    frame["day1_sensitivity_fdv_usd"] = sensitivity_day1["fdv_usd"]
    frame["day1_sensitivity_quality"] = sensitivity_day1["quality"]

    snapshot_time = pd.to_datetime(
        frame["pm_pre_tge_snapshot_time_utc"], errors="coerce", utc=True
    )
    sale_close_time = pd.to_datetime(
        frame["sale_close_utc"], errors="coerce", utc=True
    )
    has_exact_probabilities = frame["pm_pre_tge_probs"].notna()
    frame["pm_exact_snapshot_available"] = (
        snapshot_time.notna() & has_exact_probabilities
    )
    frame["pm_actionable_signal_available"] = (
        frame["pm_actionability"].eq("actionable")
        & frame["pm_exact_snapshot_available"]
        & snapshot_time.le(sale_close_time)
    )

    parsed_proxy = frame["pm_probs_proxy"].map(parse_pm_thresholds)
    frame["pm_proxy_threshold_count"] = parsed_proxy.map(len)
    frame["pm_proxy_median_floor_fdv_usd"] = parsed_proxy.map(proxy_median_floor)
    frame["pm_proxy_median_floor_multiple"] = (
        frame["pm_proxy_median_floor_fdv_usd"] / frame["sale_fdv_usd"]
    )

    return frame
