#!/usr/bin/env python3
"""Build the measured hotel-to-venue walking matrix (task Y3, session f0d7de66).

Reads two dated captures and writes data/f0d7de66/walks.json:

  data/raw/f0d7de66-geocode.txt   OpenStreetMap/Nominatim point for each Strip property
  data/raw/f0d7de66-osrm.txt     OSRM foot-distance matrix + independent single-pair routes

Nothing is invented. The only number computed here is the minute count, from the measured route
length at a stated pace:

    minutes = ceil(route_length_m / 80 m per minute)      # 4.8 km/h, a normal walking pace

Why the pace and not the routing server's own durations: this server returned foot durations of
4-8 m/s for these pairs, which is not walking speed, so only its route lengths are trustworthy.
That is recorded in the capture header and in the output meta.

Every check below is a hard failure (nothing is written) rather than a warning:

  * the matrix response has to say code Ok and cover every (hotel, destination) cell
  * each single-pair cross-check has to return exactly the matrix distance for the same pair
  * the coordinates the two responses snapped the route to have to agree - a pair measured from a
    different point than the matrix is not the same walk
  * every point the matrix indexes has to be the point the geocode capture recorded for it
  * every venue that carries events has to have a measured destination property

Usage: python3 tools/f0d7de66_walks.py
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "f0d7de66"

PACE_M_PER_MIN = 80.0          # 4.8 km/h, a normal walking pace
LIMIT_MIN = 30                 # the trip's own rule: a day is only usable if the walk fits
SNAP_WARN_M = 150.0            # call out a route whose end was snapped further than this
SNAP_MAX_M = 250.0             # beyond this the route no longer describes a walk to that building
TOL_M = 0.05                   # agreement tolerance between the two responses

# Which building a poker room actually sits in, for walking purposes. The Venetian Poker Room is
# on The Palazzo level 2, so a guest of either tower is walking inside the same complex.
VENUE_PROPERTY = {"venetian": "palazzo", "wynn": "wynn", "bellagio": "bellagio", "caesars": "caesars"}
VENUE_NAME = {"venetian": "The Venetian Poker Room", "wynn": "Wynn Las Vegas Poker",
              "bellagio": "Bellagio Poker Room", "caesars": "Caesars Palace Poker Room"}
# Buildings one landlord calls one complex: no street crossing, no public-way measurement needed.
SAME_COMPLEX = [frozenset({"venetian", "palazzo"}), frozenset({"wynn", "encore"})]


def metres_between(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance, used only to prove a response's snapped point belongs to the
    coordinate this session asked about - not a route length."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def read_lines(path: Path):
    out, in_comment = [], False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if in_comment:                      # still inside the capture's header comment
            if line.endswith("-->"):
                in_comment = False
            continue
        if line.startswith("<!--"):
            in_comment = not line.endswith("-->")
            continue
        try:
            out.append((n, json.loads(line)))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path.name}:{n}: not valid JSON ({exc})")
    return out


def main() -> int:
    problems: list[str] = []

    geo = {}
    for n, rec in read_lines(RAW / "f0d7de66-geocode.txt"):
        if "id" not in rec:
            problems.append(f"geocode line {n}: no id")
            continue
        if rec["id"] in geo:
            problems.append(f"geocode: duplicate id {rec['id']} (line {n})")
        geo[rec["id"]] = rec

    rows = read_lines(RAW / "f0d7de66-osrm.txt")
    matrix = next((r for _, r in rows if r.get("kind") == "matrix"), None)
    pair_rows = [(n, r) for n, r in rows if r.get("kind") == "pair"]
    if matrix is None:
        raise SystemExit("no matrix line in data/raw/f0d7de66-osrm.txt")
    if matrix.get("code") != "Ok":
        problems.append(f"matrix response code is {matrix.get('code')!r}, not Ok")

    src_ids, dst_ids, dist = matrix["source_ids"], matrix["destination_ids"], matrix["distances"]
    if len(dist) != len(src_ids) or any(len(r) != len(dst_ids) for r in dist):
        raise SystemExit(f"matrix shape {len(dist)}x{len(dist[0])} is not "
                         f"{len(src_ids)} sources x {len(dst_ids)} destinations")
    snap_src, snap_dst = matrix["snapped_sources"], matrix["snapped_destinations"]
    if len(snap_src) != len(src_ids) or len(snap_dst) != len(dst_ids):
        problems.append("the snapped-point lists do not line up with the id lists")

    for label, ids, snapped in (("source", src_ids, snap_src), ("destination", dst_ids, snap_dst)):
        for i, (pid, (lon, lat, off)) in enumerate(zip(ids, snapped)):
            g = geo.get(pid)
            if not g:
                problems.append(f"matrix {label}[{i}] = {pid}: not in the geocode capture")
                continue
            # OSRM snaps an input coordinate to the nearest routable point, so the response's
            # location is expected to differ from the geocoded point. What has to hold is that the
            # gap equals the distance the response itself reports, and that the gap is small
            # enough for the route to still be a route to that building.
            gap = metres_between(g["lat"], g["lon"], lat, lon)
            if abs(gap - off) > 15.0:
                problems.append(f"matrix {label}[{i}] = {pid}: the snapped point is {gap:.0f} m from the "
                                f"geocoded point but the response says {off:.0f} m, so this matrix cannot "
                                f"be shown to describe the recorded points")
            if off > SNAP_MAX_M:
                problems.append(f"matrix {label}[{i}] = {pid}: snapped {off:.0f} m away, more than the "
                                f"{SNAP_MAX_M:.0f} m allowed for a building-to-building walk")
            g["_snapped_off_m"] = off

    cell = {(s, d): round(float(dist[si][di]), 1)
            for si, s in enumerate(src_ids) for di, d in enumerate(dst_ids)}

    checked = 0
    for n, p in pair_rows:
        key = (p["from"], p["to"])
        if key not in cell:
            problems.append(f"osrm line {n}: pair {p['from']}->{p['to']} is not a matrix cell")
            continue
        if abs(float(p["distance_m"]) - cell[key]) > TOL_M:
            problems.append(f"osrm line {n}: {p['from']}->{p['to']} route says {p['distance_m']} m "
                            f"but the matrix says {cell[key]} m for the same pair")
        s0, s1 = snap_src[src_ids.index(key[0])], snap_dst[dst_ids.index(key[1])]
        want = ((round(float(s0[0]), 6), round(float(s0[1]), 6)),
                (round(float(s1[0]), 6), round(float(s1[1]), 6)))
        got = tuple((round(float(wp[0]), 6), round(float(wp[1]), 6)) for wp in p["waypoints"])
        if got != want:
            problems.append(f"osrm line {n}: {p['from']}->{p['to']} snapped to {got}, the matrix "
                            f"snapped the same two points to {want}")
        checked += 1
    if not checked:
        problems.append("no single-pair cross-checks in the capture; refusing to trust the matrix alone")

    site = json.loads((ROOT / "data" / "site-events.json").read_text(encoding="utf-8"))
    event_venues = sorted({e.get("venue") for e in site["events"] if e.get("venue")})
    for v in event_venues:
        prop = VENUE_PROPERTY.get(v)
        if prop and prop not in dst_ids:
            problems.append(f"venue {v} carries events but its building {prop} has no column in the matrix")

    if problems:
        print("REFUSING TO WRITE:")
        for pr in problems:
            print("  -", pr)
        return 1

    def minutes(metres: float) -> int:
        return math.ceil(metres / PACE_M_PER_MIN)

    pairs = []
    for hotel in src_ids:
        for venue, prop in VENUE_PROPERTY.items():
            m = cell.get((hotel, prop))
            if m is None:
                continue
            on_site = (hotel == prop) or (frozenset({hotel, prop}) in SAME_COMPLEX)
            mins = None if on_site else minutes(m)
            caveats = []
            if on_site:
                caveats.append("one complex: the route is inside the property, so it is not a "
                               "street walk and the distance is building-point to building-point")
            for pid, what in ((hotel, "the hotel"), (prop, "the poker room's building")):
                off = geo.get(pid, {}).get("_snapped_off_m", 0)
                if off and off > SNAP_WARN_M:
                    caveats.append(f"the route's end at {what} was snapped {round(off)} m from the "
                                   f"recorded property point, so the length includes that detour")
            pairs.append({
                "hotel_id": hotel,
                "hotel": geo[hotel]["name"],
                "venue_id": venue,
                "venue": VENUE_NAME[venue],
                "measured_between": f"{geo[hotel]['name']} point -> {geo[prop]['name']} point",
                "distance_m": m,
                "minutes": mins,
                "meets_30_min": ("not applicable (on-site)" if on_site
                                 else ("yes" if mins <= LIMIT_MIN else "no")),
                "status": ("same complex, no public-way route to measure" if on_site else
                           "route length measured from the property points in the geocode capture "
                           "(building centroids, not doors); minutes are an estimate at a stated pace"),
                "basis": (f"OpenStreetMap foot-route length {m} m between the two property points, "
                          f"divided by {PACE_M_PER_MIN:.0f} m/min (4.8 km/h) and rounded up"
                          if not on_site else
                          f"OpenStreetMap foot-route length {m} m between the two property points, "
                          f"recorded for completeness only"),
                "official": False,
                "source": "https://router.project-osrm.org",
                "point_source": geo[hotel].get("query_url"),
                "retrieved": "2026-11-17",
                "caveats": caveats,
            })

    per_hotel = []
    for hotel in src_ids:
        mine = [p for p in pairs if p["hotel_id"] == hotel]
        measured = sorted([p for p in mine if p["minutes"] is not None], key=lambda p: p["minutes"])
        per_hotel.append({
            "hotel_id": hotel,
            "hotel": geo[hotel]["name"],
            "on_site_at": sorted({p["venue_id"] for p in mine if p["minutes"] is None}),
            "venues_within_30_min": sorted({p["venue_id"] for p in measured if p["meets_30_min"] == "yes"}),
            "venues_over_30_min": sorted({p["venue_id"] for p in measured if p["meets_30_min"] == "no"}),
            "min_minutes": measured[0]["minutes"] if measured else None,
            "max_minutes": measured[-1]["minutes"] if measured else None,
        })

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = {
        "meta": {
            "generated": now,
            "session": "f0d7de66",
            "task": "Y3 - walking-route check feeding the 30-minute rule",
            "rule": (f"a hotel is usable for a day only if the walk to the room hosting that day's "
                     f"events fits inside {LIMIT_MIN} minutes"),
            "method": ("OpenStreetMap foot-route length between each property's building point and each "
                       "event room's building point, converted to minutes at a stated pace"),
            "pace_m_per_min": PACE_M_PER_MIN,
            "limit_minutes": LIMIT_MIN,
            "why_not_the_server_durations": ("the demo router's foot durations came back at 4-8 m/s, which "
                                             "is not walking speed, so only its route lengths were used"),
            "official": False,
            "official_note": ("no Strip property publishes a door-to-door walking time to another property's "
                              "poker room, so nothing here is an official figure: it is a measurement from "
                              "public mapping data, dated, and reproducible from the two captures"),
            "venues_with_events_in_the_snapshot": event_venues,
            "cross_checks": {"pairs_rerouted_independently": checked, "tolerance_m": TOL_M,
                             "all_agreed": True},
            "captures": ["data/raw/f0d7de66-geocode.txt", "data/raw/f0d7de66-osrm.txt"],
            "credits": "Map data (c) OpenStreetMap contributors, ODbL, http://osm.org/copyright",
        },
        "pairs": pairs,
        "per_hotel": per_hotel,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "walks.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")

    over = [p for p in pairs if p["meets_30_min"] == "no"]
    print(f"pairs={len(pairs)} cross-checked={checked} over-{LIMIT_MIN}-min={len(over)} "
          f"on-site={sum(1 for p in pairs if p['minutes'] is None)} "
          f"venues-with-events={','.join(event_venues)}")
    for h in per_hotel:
        print(f"  {h['hotel_id']:10s} on-site:{','.join(h['on_site_at']) or '-':9s} "
              f"<=30:{','.join(h['venues_within_30_min']) or '-':22s} >30:{','.join(h['venues_over_30_min']) or '-'}")
    print(f"wrote {OUT / 'walks.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
