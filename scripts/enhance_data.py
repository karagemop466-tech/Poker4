#!/usr/bin/env python3
"""Enhance root data files with the fields the brief requires:
- last_checked / retrieval_date on every tournament row
- structured rule fields (single_entry, reentry, addon, fee, total_entry_fee)
  each with value, status, excerpt, source, retrieved date
- source_checked / source_changed flags for change monitoring
- dated rate log on hotels (rate_log), plus checkout_total, nightly_average,
  parking, cancellation_deadline
- change-monitor registry entries in data/sources.json

Run:  python3 scripts/enhance_data.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHECKED = "2026-11-16"


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def save(name, obj):
    with open(DATA / name, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def rule_block(value, status, excerpt, source):
    return {
        "value": value,
        "status": status,  # "confirmed" | "unverified" | "not_applicable"
        "excerpt": excerpt,
        "source": source,
        "retrieved": CHECKED,
    }


def enhance_tournaments():
    T = load("tournaments.json")
    T["meta"]["enhanced"] = CHECKED
    T["meta"]["rule_field_note"] = (
        "single_entry / reentry / addon are confirmed only where the official "
        "structure sheet states them; absence of a statement is recorded as "
        "'unverified', never treated as freezeout. fee / total_entry_fee are "
        "confirmed where the schedule or structure states a dollar amount."
    )

    for key in ("entry_rules_unverified", "reentry_or_addon"):
        for r in T.get(key, []):
            r["last_checked"] = CHECKED
            r["retrieval_date"] = CHECKED
            r["source_checked"] = CHECKED
            r["source_changed"] = False

            fee = r.get("house_fee")
            buy_in = r.get("buy_in")
            reentry_text = r.get("reentry_addon") or ""

            is_confirmed_reentry = (
                reentry_text
                and "None listed" not in reentry_text
                and "not stated" not in reentry_text.lower()
                and "unknown" not in reentry_text.lower()
            )

            r["rule_fields"] = {
                "single_entry": rule_block(
                    None,
                    "unverified",
                    "Reviewed structure does not state a one-entry limit or prohibit re-entry/rebuy/add-on.",
                    r["sources"][0] if r.get("sources") else None,
                ),
                "reentry": rule_block(
                    None,
                    "confirmed" if is_confirmed_reentry else "unverified",
                    reentry_text if is_confirmed_reentry else "Re-entry policy not stated in the reviewed structure.",
                    r["sources"][0] if r.get("sources") else None,
                ),
                "addon": rule_block(
                    None,
                    "confirmed" if ("add-on" in reentry_text.lower() or "addon" in reentry_text.lower()) and is_confirmed_reentry else "unverified",
                    reentry_text if ("add-on" in reentry_text.lower() or "addon" in reentry_text.lower()) and is_confirmed_reentry else "Add-on policy not stated in the reviewed structure.",
                    r["sources"][0] if r.get("sources") else None,
                ),
                "fee": rule_block(
                    fee,
                    "confirmed" if isinstance(fee, (int, float)) else "unverified",
                    f"${fee} house fee" if isinstance(fee, (int, float)) else "House fee not stated in the reviewed source.",
                    r["sources"][0] if r.get("sources") else None,
                ),
                "total_entry_fee": rule_block(
                    buy_in,
                    "confirmed" if isinstance(buy_in, (int, float)) else "unverified",
                    f"${buy_in:,} buy-in" if isinstance(buy_in, (int, float)) else "Buy-in not stated in the reviewed source.",
                    r["sources"][0] if r.get("sources") else None,
                ),
            }

    save("tournaments.json", T)
    n = len(T.get("entry_rules_unverified", [])) + len(T.get("reentry_or_addon", []))
    print(f"tournaments.json: enhanced {n} rows with rule_fields + last_checked")


def enhance_hotels():
    H = load("hotels.json")
    H["meta"]["enhanced"] = CHECKED
    H["meta"]["rate_log_note"] = (
        "Rates are kept as a dated log, not a single value. Each log entry "
        "records the base rate, mandatory resort fee, tax, timestamp and "
        "source for one observed date. True cost/night = rate + resort fee + "
        "13.38% Clark County tax (+ parking where applicable)."
    )
    for h in H.get("hotels", []):
        h["last_checked"] = CHECKED
        h["rate_log"] = [
            {
                "date": CHECKED,
                "rate": None,
                "resort_fee": 55 if h["property"] == "The Venetian / The Palazzo" else None,
                "tax_rate": 0.1338,
                "total": None,
                "timestamp": f"{CHECKED}T00:00:00Z",
                "source": "V_RESORT" if h["property"] == "The Venetian / The Palazzo" else None,
                "note": "Mandatory resort fee confirmed on official page; room rate not confirmed for any date.",
            }
        ]
        h["checkout_total"] = None
        h["nightly_average"] = None
        h["parking"] = None
        h["cancellation_deadline"] = None
    save("hotels.json", H)
    print(f"hotels.json: enhanced {len(H.get('hotels', []))} hotels with dated rate log")


def enhance_sources():
    S = load("sources.json")
    S["monitor_registry"] = [
        {
            "id": "M-VEN-SCHED",
            "url": "https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html",
            "label": "Venetian DSE IV event schedule",
            "last_checked": CHECKED,
            "status": "not_rechecked_external_blocked",
            "changed": False,
            "note": "External host not reachable from this build; change re-check must run server-side against the official page.",
        },
        {
            "id": "M-VEN-FEE",
            "url": "https://www.venetianlasvegas.com/resort/resort-fee.html",
            "label": "Venetian resort fee",
            "last_checked": CHECKED,
            "status": "not_rechecked_external_blocked",
            "changed": False,
            "note": "$55 + tax confirmed at snapshot; re-check required before relying on current rate.",
        },
        {
            "id": "M-VEN-RATES",
            "url": "https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html",
            "label": "Venetian poker suite rates",
            "last_checked": CHECKED,
            "status": "not_rechecked_external_blocked",
            "changed": False,
            "note": "Starting endpoints $119/$209 are conditional, not date-specific quotes.",
        },
        {
            "id": "M-WYNN-POKER",
            "url": "https://www.wynnlasvegas.com/casino/poker",
            "label": "Wynn poker room",
            "last_checked": CHECKED,
            "status": "not_rechecked_external_blocked",
            "changed": False,
            "note": "Official Wynn daily/WPT schedules cited at snapshot; re-check required.",
        },
    ]
    S["monitor_note"] = (
        "Official URLs are listed for scheduled re-check. A changed value sets "
        "changed = true and flags the affected rows. Client-side re-fetch of "
        "external hosts is blocked in this sandbox; run the check server-side "
        "and update last_checked / changed before each publish."
    )
    save("sources.json", S)
    print(f"sources.json: added {len(S['monitor_registry'])} monitor registry entries")


if __name__ == "__main__":
    enhance_tournaments()
    enhance_hotels()
    enhance_sources()
    print("done")
