#!/usr/bin/env python3
"""Rebuild hotels.json walk_to_venues from ONE clearly labelled OSRM 8x8 matrix.

Fixes two defects in the first pass:
  1. it stored OSRM seconds in a field called "minutes" (926 m -> 2.4 "min");
  2. destination indices were mismatched, so labels were wrong (Palazzo->TI was
     recorded as 2484.9 m when the labelled matrix gives 972.2 m).

Matrix source (MAP_OSRM_8, fetched 2026-11-17), node order:
  0 Palazzo 36.1241843,-115.1682710   4 TI tram   36.1245303,-115.1729076
  1 Venetian tower 36.1217073,-115.1693352   5 Harrah's 36.1193033,-115.1711625
  2 Wynn 36.1266219,-115.1654043      6 Caesars   36.1166277,-115.1767568
  3 Encore 36.1289345,-115.1653620    7 Bellagio  36.1131149,-115.1770065
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "v2", "hotels.json")
H = json.load(open(P))

SPEED, BUFFER = 4.8, 1.25          # km/h, then a 25% allowance for crossings/elevators/corridors
def mins(m):
    return round(m / 1000.0 / SPEED * 60 * BUFFER, 1)

NODES = ["Palazzo", "Venetian tower", "Wynn", "Encore", "TI tram", "Harrah's", "Caesars", "Bellagio"]
COORD = [(36.1241843, -115.1682710), (36.1217073, -115.1693352),
         (36.1266219, -115.1654043), (36.1289345, -115.1653620),
         (36.1245303, -115.1729076), (36.1193033, -115.1711625),
         (36.1166277, -115.1767568), (36.1131149, -115.1770065)]
D8 = [
 [0,     1092.4, 1021.5, 925.9,  972.2,  1808.8, 2484.9, 2532.1],
 [410,   0,      1163.3, 1067.7, 590.2,  1106.3, 1402.5, 1829.6],
 [1126.1,1352.2, 0,      95.6,   1232,   2068.5, 2744.7, 2791.8],
 [1030.4,1256.5, 95.6,   0,      1136.3, 1972.9, 2649.1, 2696.2],
 [843.7, 705.6,  1108.3, 1012.7, 0,      1422,   1869.1, 2145.3],
 [832.9, 725.3,  1586.2, 1490.6, 1013.1, 0,      1805.8, 2232.9],
 [1656.8,1549.3, 2807.9, 2712.3, 1837,   1081.9, 0,      1903.8],
 [1861.9,1754.3, 2615.2, 2519.6, 2042,   1287,   1745.8, 0],
]
IX = {n: i for i, n in enumerate(NODES)}

# The poker room of each venue (Venetian room is in the Palazzo; Wynn room is in Encore)
VENUE_NODE = {"Venetian": "Palazzo", "Wynn": "Encore", "Caesars Palace": "Caesars", "Bellagio": "Bellagio"}
# Where each hotel's own tower sits on the matrix
HOTEL_NODE = {"venetian": "Venetian tower", "wynn": "Wynn", "treasure_island": "TI tram",
              "harrahs": "Harrah's", "caesars_palace": "Caesars", "bellagio": "Bellagio"}


def gc(a, b):
    R = 6371000.0
    p1, l1 = map(math.radians, a); p2, l2 = map(math.radians, b)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


for h in H["hotels"]:
    o = HOTEL_NODE[h["id"]]
    out = []
    for venue, vnode in VENUE_NODE.items():
        if o == vnode:
            out.append({"venue": venue, "same_property": True, "metres": 0, "minutes": 0,
                        "under_30": True, "status": "same_property",
                        "method": "same property — the poker room is inside this resort"})
            continue
        d = D8[IX[o]][IX[vnode]]
        back = D8[IX[vnode]][IX[o]]
        m = mins(d)
        asym = abs(d - back) / max(d, back)
        rec = {"venue": venue,
               "origin_node": o, "venue_node": vnode,
               "osrm_m": d, "osrm_m_reverse": back,
               "reciprocal_difference_pct": round(asym * 100),
               "great_circle_m": round(gc(COORD[IX[o]], COORD[IX[vnode]])),
               "minutes": m, "under_30": m <= 30,
               "status": "route_asymmetric" if asym > 0.20 else "route_consistent",
               "method": "OSRM foot route %s -> %s, %s m; minutes = m / 4.8 km/h * 60 * 1.25"
                         % (o, vnode, format(d, ","))}
        out.append(rec)
    # keep the existing extra labels for reference but replace the computed core
    h["walk_to_venues"] = out

H["meta"]["walk_note"] = (
    "One labelled OSRM 8x8 distance matrix (MAP_OSRM_8, 2026-11-17) supplies every route figure. "
    "Minutes = metres / 4.8 km/h * 60 * 1.25; the 25% allowance covers street crossings, the pedestrian "
    "bridges over Las Vegas Blvd, elevators and casino corridors. The same formula is applied to every pair. "
    "Each pair also records the reverse-direction route: where the two differ by more than 20% the row is "
    "marked route_asymmetric and the reverse distance is shown, because the difference can be a real one-way "
    "pedestrian funnel or a geocoder snap artefact, and silently choosing one number would hide that. These are "
    "NOT Google or Apple Maps numbers, no casino publishes walking times, and none of it models the indoor walk "
    "from your tower to the poker room."
)
H["meta"]["walk_formula"] = "minutes = osrm_m / 1000 / 4.8 * 60 * 1.25"
H["meta"]["walk_status_vocabulary"] = ["route_consistent", "route_asymmetric", "same_property"]
json.dump(H, open(P, "w"), indent=1)

for h in H["hotels"]:
    print(h["id"])
    for w in h["walk_to_venues"]:
        if w["status"] == "same_property":
            print("   %-16s same property" % w["venue"])
        else:
            print("   %-16s %5.1f min  %6s m (rev %6s, diff %2d%%) gc=%5d  %s"
                  % (w["venue"], w["minutes"], w["osrm_m"], w["osrm_m_reverse"],
                     w["reciprocal_difference_pct"], w["great_circle_m"],
                     "" if w["under_30"] else "OVER 30"))
