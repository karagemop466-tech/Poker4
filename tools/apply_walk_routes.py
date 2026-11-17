#!/usr/bin/env python3
"""Port the verified Google Maps walking routes into the canonical config.

The measurement log this reads is `data/verify/walking_routes_2026-11-17.tsv`,
which was produced by opening each Google Maps walking-directions route for the
named hotel/venue pair and reading the printed duration and distance.

Nothing here is invented: every minutes/distance value comes from that log, and
every row keeps the route URL, the route note and the date it was read so a
reader can re-open the route and check it.  Pairs the log does not cover stay
unmeasured and keep their "unverified" wording — silence is never a pass.

Two things are corrected rather than copied:

  * a measured route for a pair REPLACES the unmeasured placeholder for that
    same pair (Treasure Island -> Venetian is one route, not two rows);
  * the on-site entries are re-worded to describe the lobby-to-poker-room walk
    they actually are.  The earlier text argued that Wynn -> Venetian was "not
    a plausible walk-to-play pairing" on a ~2.2-mile Strip frontage; the route
    that was actually opened measures 13 minutes via Wynn Main Gate Drive, so
    the guess is dropped rather than left standing next to the measurement.

Run:  python3 tools/apply_walk_routes.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "verify" / "walking_routes_2026-11-17.tsv"
CFG = ROOT / "data" / "poker4.json"

# The log prints property names; map them onto the canonical hotel/venue ids.
HOTEL_ID = {
    "Wynn Las Vegas": "wynn",
    "Bellagio": "bellagio",
    "ARIA": "aria",
    "Caesars Palace": "caesars",
    "Treasure Island": "ti",
    "Harrah's Las Vegas": "harrahs",
    "Horseshoe Las Vegas": "horseshoe",
}
VENUE_ID = {"Venetian": "venetian", "Wynn": "wynn"}

# The lobby-to-poker-room walk inside a property: no route measures it and no
# operator publishes it, so it stays unmeasured and is never scored as a pass.
ON_SITE = {
    ("venetian", "venetian"): (
        "same property — the poker room is inside the Venetian/Palazzo complex (Palazzo level 2). "
        "No route measures the lobby-to-room walk; the operator publishes directions, not minutes."),
    ("palazzo", "venetian"): (
        "same complex — the poker room is on Palazzo level 2 and is reached from either tower. "
        "No route measures the lobby-to-room walk."),
    ("wynn", "wynn"): (
        "same property — the poker room is inside the Wynn/Encore complex. No route measures the "
        "lobby-to-room walk and the operator publishes no minute count."),
    ("encore", "wynn"): (
        "same resort campus — Encore is connected to the Wynn tower that hosts the poker room. "
        "No route measures the lobby-to-room walk."),
    ("bellagio", "bellagio"): (
        "same property — the poker room is inside the Bellagio. No route measures the lobby-to-room walk."),
    ("caesars", "caesars"): (
        "same property — the poker room is inside Caesars Palace. No route measures the lobby-to-room walk."),
    ("aria", "aria"): (
        "same property — the poker room is inside ARIA. No route measures the lobby-to-room walk. "
        "The Aria Express tram is free but does not reach the Venetian."),
    ("horseshoe", "others"): (
        "same property — the poker room is inside Horseshoe Las Vegas. No route measures the lobby-to-room walk."),
    ("harrahs", "others"): (
        "same property — the poker room is inside Harrah's Las Vegas. No route measures the lobby-to-room walk."),
    ("ti", "venetian"): (
        "Treasure Island has no poker room; the room a guest would play is The Venetian across the Strip. "
        "That crossing is the route measured below."),
}

ON_SITE_MEETS = "not applicable (on-site)"
READ = {"verified", "over_30"}


def measured_pairs() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with LOG.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r.get("limit_result") not in READ:
                continue
            minutes = int(r["walk_minutes"])
            vkey = VENUE_ID.get(r["venue"])
            if vkey is None:
                continue
            if r["hotel"] == "The Venetian / The Palazzo":
                hids = ["venetian", "palazzo"]
            else:
                hid = HOTEL_ID.get(r["hotel"])
                hids = [hid] if hid else []
            for hid in hids:
                out[(hid, vkey)] = {
                    "minutes": minutes,
                    "distance": r.get("distance") or "",
                    "meets_30_min": ("yes — %d min measured (Google Maps)" % minutes) if minutes <= 30
                                    else ("no — %d min measured, over the 30-minute limit" % minutes),
                    "status": (r.get("note") or "").strip(),
                    "source": r.get("route_source") or "",
                    "source_type": "maps",
                    "method": "Google Maps walking directions, opened and read on %s" % (r.get("checked") or ""),
                    "measured_on": r.get("checked") or "",
                }
    return out


def main() -> int:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    hotels = {h["id"]: h for h in cfg["hotels"]}
    meas = measured_pairs()

    for hid, h in hotels.items():
        pairs: dict[str, dict] = {}

        # 1. the property's own room (or, for Treasure Island, the room it would play)
        for vid in h.get("venue_ids") or []:
            note = ON_SITE.get((hid, vid), "")
            pairs[vid] = {
                "venue_id": vid,
                "minutes": None,
                "meets_30_min": ON_SITE_MEETS,
                "status": note,
                "source": (h.get("walk") or {}).get("source") or "",
                "source_type": "operator" if (h.get("walk") or {}).get("source") else "",
            }

        # 2. every measured cross-property route (replaces the placeholder for the same pair)
        for (mh, mv), rec in sorted(meas.items()):
            if mh != hid:
                continue
            pairs[mv] = {"venue_id": mv, **rec}

        h["walks"] = [pairs[v] for v in sorted(pairs)]

        # 3. the hotel's headline walk is the route to the room it would actually
        #    play — the room in its own venue_ids.  For Treasure Island that is
        #    the Venetian across the Strip, and the measured 6 minutes is the
        #    headline; for every other property it is the room inside its own
        #    walls, which stays unmeasured.
        own_vids = list(h.get("venue_ids") or [])
        headline = next((p for p in h["walks"] if p["venue_id"] in own_vids), h["walks"][0])
        h["walk"] = {
            "minutes": headline.get("minutes"),
            "meets_30_min": headline.get("meets_30_min"),
            "status": headline.get("status"),
            "source": headline.get("source"),
        }

    for f in cfg["flags"]:
        if f["id"] == "F3":
            f["severity"] = "partially-closed"
            f["item"] = ("Walking minutes now exist for the cross-property routes; the two on-site internal "
                         "walks are still unmeasured")
            f["detail"] = (
                "Every cross-property hotel->Venetian and hotel->Wynn route was opened in Google Maps walking "
                "directions and read on 2026-11-17; the durations and distances are in "
                "data/verify/walking_routes_2026-11-17.tsv and on the hotels page. A routing-engine duration is "
                "not an operator-published figure, so each row says so. Still open: the lobby-to-poker-room walk "
                "inside The Venetian/Palazzo and inside Wynn/Encore, which no route measures and no property "
                "publishes."
            )
            f["sources"] = ["https://www.venetianlasvegas.com/resort/casino/poker.html",
                            "https://www.wynnlasvegas.com/casino/poker"]
        elif f["id"] == "F18":
            f["severity"] = "closed-with-source"
            f["item"] = "The published walking minutes now carry a source: the Google Maps walking route that was read"
            f["detail"] = (
                "The earlier landing page listed TI 6 min, Harrah's 6, Caesars 12, Wynn 13, Horseshoe 16, "
                "Bellagio 21 and ARIA 31 as 'verified' with no source at all. The numbers themselves check out "
                "against the routes that were opened on 2026-11-17, and each row now links the exact Google Maps "
                "walking-directions URL with the date it was read, so the claim can be re-checked. They are "
                "labelled as map measurements rather than as official property figures. One earlier guess was "
                "withdrawn: the site had argued Wynn->Venetian was 'not a plausible walk-to-play pairing' on a "
                "~2.2-mile Strip frontage, and the route that was actually opened measures 13 minutes."
            )
            f["sources"] = ["https://www.google.com/maps/dir/?api=1&origin=Treasure+Island+Las+Vegas,"
                            "+3300+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&destination=The+Venetian+Resort,"
                            "+3355+Las+Vegas+Blvd+S,+Las+Vegas,+NV+89109&travelmode=walking"]

    cfg["walk_policy"]["verified_minutes_source"] = (
        "Google Maps walking directions, opened and read on 2026-11-17 for every cross-property hotel->Venetian "
        "and hotel->Wynn pair; the route URL, the printed duration, the printed distance and the read date are "
        "kept per pair. A routing-engine duration is a measurement, not an operator-published figure, and the "
        "on-site internal walks (The Venetian/Palazzo and Wynn/Encore) have no route and stay unmeasured."
    )
    cfg["walk_policy"]["how_to_close"] = (
        "Re-open each route URL in data/verify/walking_routes_2026-11-17.tsv and record the new duration and date, "
        "or take a lobby-to-poker-room walk on site and publish the measurement with the date it was taken. "
        "Update the pairs in data/poker4.json and rebuild; the rows update with the run."
    )

    CFG.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_pairs = sum(len(h.get("walks") or []) for h in cfg["hotels"])
    n_meas = sum(1 for h in cfg["hotels"] for p in (h.get("walks") or []) if p.get("minutes"))
    print(f"walk pairs: {n_pairs} · measured: {n_meas} · hotels: {len(cfg['hotels'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
