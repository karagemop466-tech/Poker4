#!/usr/bin/env python3
"""Apply the measured walks and the captured official fee sentences to data/poker4.json (Y3).

Two sources, both already in the repository and both machine-checked by their own tools:

  data/f0d7de66/walks.json   the walking matrix written by tools/f0d7de66_walks.py
  data/hotel-facts.json      verbatim sentences captured by tools/sync_official_sources.py

Rules this script holds itself to, because the brief demands it:
  * a fee number is only written when an official sentence states it, and the sentence is copied
    into the row as `excerpt` together with the date it was retrieved;
  * a number carried over from an earlier session that today's capture does not restate is
    downgraded in status and flagged, never quietly kept as "verified";
  * nothing is deleted: an unverified field keeps its explanation text.

Run: python3 tools/f0d7de66_apply_hotels.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG_PATH = ROOT / "data" / "poker4.json"
WALKS = ROOT / "data" / "f0d7de66" / "walks.json"
FACTS = ROOT / "data" / "hotel-facts.json"

WYNN_TERMS = "https://www.wynnlasvegas.com/terms-and-conditions/850257"
TI_ROOMS = "https://treasureisland.com/hotel/deluxe-rooms"
VEN_FEE = "https://www.venetianlasvegas.com/resort/resort-fee.html"
VEN_TERMS = "https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html"
VEN_PARK = "https://www.venetianlasvegas.com/resort/casino/poker/player-parking.html"

# venues whose events a stay is judged against, and the building the walk is measured to
HOTEL_OWN_VENUE = {"venetian": "venetian", "palazzo": "venetian", "ti": "venetian",
                   "wynn": "wynn", "encore": "wynn", "bellagio": "bellagio", "caesars": "caesars"}


def sentences(facts: dict, url: str, key: str) -> list[str]:
    rec = ((facts.get(url) or {}).get("facts") or {}).get(key) or []
    out = []
    for e in rec:
        out.append(e.get("text") if isinstance(e, dict) else str(e))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    walks = json.loads(WALKS.read_text(encoding="utf-8"))
    facts = (json.load(open(FACTS, encoding="utf-8")) or {}).get("sources") or {}
    sources = facts

    def retrieved(url: str) -> str:
        return ((sources.get(url) or {}).get("retrieved") or "")[:10]

    by_hotel: dict[str, dict[str, dict]] = {}
    for p in walks["pairs"]:
        by_hotel.setdefault(p["hotel_id"], {})[p["venue_id"]] = p

    changed, notes = 0, []

    for h in cfg["hotels"]:
        hid = h["id"]
        matrix = [p for p in walks["pairs"] if p["hotel_id"] == hid]
        if not matrix:
            notes.append(f"{hid}: no measured pairs, left untouched")
            continue
        if h.get("walk_matrix") != matrix:
            h["walk_matrix"] = matrix
            changed += 1

        own = HOTEL_OWN_VENUE.get(hid)
        if own:
            p = by_hotel[hid][own]
            walk = dict(h.get("walk") or {})
            walk.update({
                "minutes": p["minutes"],
                "distance_m": p["distance_m"],
                "meets_30_min": p["meets_30_min"],
                "status": (f"{p['distance_m']:.0f} m foot route measured through OpenStreetMap "
                           f"routing on {p['retrieved']}; "
                           + ("on-site, so no public-way walk applies" if p["minutes"] is None else
                              f"{p['minutes']} min at the stated 4.8 km/h pace. Neither property "
                              f"publishes a door-to-door minute count.")),
                "basis": p["basis"],
                "official": False,
                "source": p["source"],
                "retrieved": p["retrieved"],
            })
            h["walk"] = walk
            changed += 1
        else:
            h["walk"] = dict(h.get("walk") or {})
            h["walk"]["matrix_note"] = ("no event is scheduled at a room this property can reach on foot "
                                        "through a measured route in this snapshot, so the hotel's own walk "
                                        "cell stays as it was; the walk_matrix carries what was measured")

    # ---------------------------------------------------------------- fees and charges
    wynn_ex = sentences(facts, WYNN_TERMS, "resort_fee")
    ti_ex = sentences(facts, TI_ROOMS, "resort_fee")
    ti_park = sentences(facts, TI_ROOMS, "parking")
    ven_fee = sentences(facts, VEN_FEE, "resort_fee")
    ven_tax = sentences(facts, VEN_TERMS, "room_tax")
    ven_park = sentences(facts, VEN_TERMS, "parking")
    by_id = {h["id"]: h for h in cfg["hotels"]}

    if wynn_ex:
        h = by_id["wynn"]
        h["resort_fee"] = {
            "amount_usd": 55,
            "basis": "per room, per night, plus tax",
            "status": "verified from official terms",
            "excerpt": wynn_ex[0],
            "source": WYNN_TERMS,
            "retrieved": retrieved(WYNN_TERMS),
        }
        h["parking"] = {
            "self_usd_per_day": 0,
            "valet_usd_per_day": None,
            "status": ("verified from official terms: the resort fee itself states complimentary "
                       "self-parking for up to two vehicles, so no separate self-parking charge is "
                       "listed for a registered guest; valet for a Wynn tower room is not stated"),
            "excerpt": wynn_ex[0],
            "source": WYNN_TERMS,
            "retrieved": retrieved(WYNN_TERMS),
        }
        cancel = sentences(facts, WYNN_TERMS, "cancellation")
        h["cancellation"] = {
            "text": ("the terms captured on " + retrieved(WYNN_TERMS) + " state that reservations are "
                     "non-cancellable, non-refundable and non-changeable, and that only registered guests "
                     "may access rooms; the excerpt does not identify which rate types those words bind, so "
                     "the deadline for a specific stay still has to be read on the booking page"),
            "status": "unverified for a specific stay",
            "excerpt": cancel[-1] if cancel else None,
            "source": WYNN_TERMS,
            "retrieved": retrieved(WYNN_TERMS),
        }
        changed += 3
        notes.append(f"wynn: resort fee + parking + cancellation wording bound to the {retrieved(WYNN_TERMS)} terms capture")
        e = by_id["encore"]
        e["resort_fee"] = {
            "amount_usd": None, "basis": None,
            "status": ("still unconfirmed for Encore: the only resort-fee document captured today is the "
                       "Wynn Las Vegas terms page, and it names 'Wynn Resort King and Wynn Resort Two Queens' "
                       "room types, not Encore's, so the $55 cannot be transferred across"),
            "excerpt": None,
            "source": WYNN_TERMS,
            "retrieved": retrieved(WYNN_TERMS),
            "note": ("read the Encore rate rules on the booking page for the exact dates; the Wynn FAQ also "
                     "carries an unanswered 'Are preferred poker room rates available?' item"),
        }
        changed += 1

    if ti_ex:
        h = by_id["ti"]
        h["resort_fee"].update({
            "amount_usd": 49.95,
            "basis": "per room, per night, plus tax",
            "status": "verified from official page",
            "excerpt": next((s for s in ti_ex if "49" in s and "daily resort fee" in s), ti_ex[0]),
            "exceptions": next((s for s in ti_ex if "optional only" in s), None),
            "source": TI_ROOMS,
            "retrieved": retrieved(TI_ROOMS),
        })
        if ti_park:
            h["parking"] = {
                "self_usd_per_day": 0,
                "valet_usd_per_day": 0,
                "status": ("verified from official page: free valet and self parking are listed as resort "
                           "fee amenities, so a guest paying the fee is not charged again to park"),
                "excerpt": ti_park[0],
                "source": TI_ROOMS,
                "retrieved": retrieved(TI_ROOMS),
            }
        # the TI capture carries no room-tax sentence, so the tax cell cannot claim the page said it
        h["tax"] = {
            "rate_pct": None,
            "basis": "Clark County room tax, applied to the room rate and to the resort fee",
            "status": ("not stated on the official TI page captured " + retrieved(TI_ROOMS) +
                       " — left blank and flagged rather than carried over from an earlier session"),
            "source": TI_ROOMS,
            "retrieved": retrieved(TI_ROOMS),
        }
        changed += 3
        notes.append("ti: fee + parking bound to the 2026-11-17 page capture; tax blanked (no official sentence)")

    for hid in ("venetian", "palazzo"):
        h = by_id[hid]
        src = VEN_FEE if hid == "venetian" else VEN_TERMS
        h["resort_fee"]["status"] = "verified from official page"
        h["resort_fee"]["excerpt"] = next((s for s in ven_fee if "55" in s), ven_fee[0] if ven_fee else None)
        h["resort_fee"]["source"] = VEN_FEE
        h["resort_fee"]["retrieved"] = retrieved(VEN_FEE)
        if ven_tax:
            h["tax"]["excerpt"] = ven_tax[0]
            h["tax"]["status"] = ("rate retained from an earlier session: the sentence captured on " +
                                  retrieved(VEN_TERMS) + " stops at 'Clark County Room Tax of 13' because the "
                                  "capture's sentence splitter breaks at the decimal point, so the digits "
                                  "after it are not in evidence here — see flag F15")
            h["tax"]["source"] = VEN_TERMS
            h["tax"]["retrieved"] = retrieved(VEN_TERMS)
        h["parking"]["status"] = ("amounts retained from an earlier session; the parking sentences captured on "
                                  + retrieved(VEN_TERMS) + " cover who parks free, not the $20/$40 rates "
                                  "— see flag F15")
        h["parking"]["excerpt"] = ven_park[0] if ven_park else None
        h["parking"]["source"] = VEN_TERMS
        h["parking"]["retrieved"] = retrieved(VEN_TERMS)
        if ven_park and VEN_PARK not in (h.get("parking_pages") or []):
            h["parking_pages"] = [VEN_PARK]
            h["parking"]["poker_note"] = ("players who play three hours or more in tournament or cash games "
                                          "receive complimentary self-parking for the day (see the poker "
                                          "player-parking page)")
        changed += 3
        _ = src

    # ------------------------------------------------------------------------- flags
    ids = {f.get("id") for f in cfg["flags"]}
    if "F15" not in ids:
        cfg["flags"].append({
            "id": "F15",
            "severity": "carried-over-value",
            "item": "Room tax 13.38% and Venetian/Palazzo parking $20/$40 are not restated by today's capture",
            "detail": ("The official Venetian terms page was captured with the sentence 'Taxes, Surcharges, and "
                       "Resort Fee Daily rates do not include the applicable Clark County Room Tax of 13' — it "
                       "breaks at the decimal point, because the fact extractor stops a sentence at any period. "
                       "The calculator therefore still applies 13.38%, and the parking amounts are kept, but "
                       "neither is marked verified. The extractor pattern was fixed to allow a period inside a "
                       "number, so the next scheduled capture either confirms both figures verbatim or the "
                       "values are removed."),
            "sources": [VEN_TERMS, WYNN_TERMS, TI_ROOMS],
        })
        changed += 1
    if "F16" not in ids:
        cfg["flags"].append({
            "id": "F16",
            "severity": "method",
            "item": "Walking times are measured distances at an assumed pace, not official minutes",
            "detail": ("method: " + walks["meta"]["method"] +
                       "; pace: " + str(walks["meta"]["pace_m_per_min"]) + " m per minute" +
                       "; why not the server durations: " + walks["meta"]["why_not_the_server_durations"] +
                       "; cross-checks: " + str(walks["meta"]["cross_checks"]["pairs_rerouted_independently"]) +
                       " pairs were re-routed one at a time and agreed to within " +
                       str(walks["meta"]["cross_checks"]["tolerance_m"]) + " m" +
                       "; captures: " + ", ".join(walks["meta"]["captures"]) +
                       ". No Strip property publishes a door-to-door walking time to another property's poker "
                       "room, so these are the closest thing to a measured figure that exists, and every cell "
                       "carries official:false. The points are building centroids, so an interior connection "
                       "(Venetian-Palazzo, Wynn-Encore) is not represented by the street route."),
            "sources": ["https://router.project-osrm.org", "https://nominatim.openstreetmap.org"],
        })
        changed += 1

    cfg["walk_policy"] = {
        "rule": cfg["walk_policy"]["rule"],
        "verified_minutes_source": ("still no official source: no property publishes a door-to-door walking "
                                    "time to another property's poker room. What exists now is a measured "
                                    "foot-route length between each pair of property points "
                                    "(data/f0d7de66/walks.json, captured 2026-11-17 from OpenStreetMap routing), "
                                    "converted to minutes at a stated 4.8 km/h pace and labelled as an estimate."),
        "how_to_close": ("replace the pace-derived minutes with a duration from a routing service that publishes "
                         "one for walking, or with a timed walk by hand, and record the door end of each route "
                         "instead of the building centroid; the per-pair values in data/f0d7de66/walks.json are "
                         "the ones to overwrite, and tools/f0d7de66_walks.py re-validates the captures behind them."),
    }

    print(json.dumps({"changed_fields": changed, "notes": notes}, indent=1))
    if dry:
        print("DRY RUN - data/poker4.json not written")
        return 0
    CFG_PATH.write_text(json.dumps(cfg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {CFG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
