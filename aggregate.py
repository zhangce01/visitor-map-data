"""Rebuild visitors.json, the data behind the visitor globe on zhangce01.github.io.

The homepage (assets/js/visitorglobe.js there) adds one to an Abacus counter
"c-<cell>-<CC>" for each day's visit, where cell is the 1 degree cell the
visitor's network is in ((floor(lat) + 90) * 360 + floor(lon) + 180, or "x"
when only the country is known) and CC its ISO country code. Abacus cannot
list its counters, so every place also signs a register: counter "cells"
hands out slot numbers and "slot-<n>" holds (cell + 1) * 676 + the country
code read as a base-26 number. This script walks the register, reads each
registered place's count, adds seed.json (visits from before the counters
existed) and writes

    {"updated": "YYYY-MM-DD", "total": visits,
     "countries": [[code, name, visits, lat, lon, places], ...],   most visits first
     "places": [[cell, code, visits], ...]}

where a country's lat/lon is the visit-weighted centre of its places. Standard
library only. It is slow on purpose: Abacus allows 30 requests per 10 seconds.
Reading a counter also renews its six-month expiry.
"""
import collections
import datetime
import json
import math
import os
import time
import urllib.error
import urllib.request

BASE = "https://abacus.jasoncameron.dev"
SPACE = "zhangce01-github-io"
PAUSE = 0.4
CELLS = 180 * 360

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "visitors.json")
SLOTS = os.path.join(HERE, "slots.json")        # slot number -> its value, so a slot is only ever read once
SEED = os.path.join(HERE, "seed.json")          # {"places": [[cell or -1, code, visits], ...]}
TABLE = os.path.join(HERE, "countries.json")    # code -> [name, lat, lon]


def get(key):
    """value of a counter, or None if it does not exist"""
    url = "%s/get/%s/%s" % (BASE, SPACE, key)
    for attempt in range(6):
        time.sleep(PAUSE)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "zhangce01.github.io visitor map"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return int(json.load(r)["value"])
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After") or 10) + 1)
                continue
            raise
    raise RuntimeError("still rate limited: " + key)


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        f.write("\n")


def place(value):
    """slot value -> (cell, code), or None if it is not one a visitor could have written"""
    cell, k = value // 676 - 1, value % 676
    if value < 0 or cell >= CELLS:
        return None
    return cell, chr(65 + k // 26) + chr(65 + k % 26)


def centre(cell):
    return cell // 360 - 90 + 0.5, cell % 360 - 180 + 0.5


def main():
    table = load(TABLE, {})

    slots = load(SLOTS, {})
    last = get("cells") or 0
    for n in range(1, last + 1):
        if str(n) in slots:
            continue
        v = get("slot-%d" % n)
        # an empty slot may still be filled by the visitor who took it; ask again next time
        if v is not None:
            slots[str(n)] = v
    dump(SLOTS, slots)

    visits = collections.Counter()
    for cell, code, n in load(SEED, {}).get("places", []):
        visits[(int(cell), code)] += int(n)
    live = sorted(set(p for p in map(place, slots.values()) if p))
    for cell, code in live:
        v = get("c-%s-%s" % ("x" if cell < 0 else cell, code))
        if v:
            visits[(cell, code)] += v

    by = {}
    for (cell, code), n in visits.items():
        c = by.setdefault(code, {"n": 0, "x": 0.0, "y": 0.0, "z": 0.0, "places": 0})
        c["n"] += n
        if cell >= 0:
            la, lo = (math.radians(d) for d in centre(cell))
            c["x"] += n * math.cos(la) * math.cos(lo)
            c["y"] += n * math.cos(la) * math.sin(lo)
            c["z"] += n * math.sin(la)
            c["places"] += 1
    countries = []
    for code, c in by.items():
        if code not in table:
            continue
        name, la, lo = table[code]
        if c["places"] and math.sqrt(c["x"] ** 2 + c["y"] ** 2 + c["z"] ** 2) > 1e-9:
            la = math.degrees(math.atan2(c["z"], math.hypot(c["x"], c["y"])))
            lo = math.degrees(math.atan2(c["y"], c["x"]))
        countries.append([code, name, c["n"], round(la, 1), round(lo, 1), c["places"]])
    countries.sort(key=lambda c: (-c[2], c[1]))
    places = sorted([cell, code, n] for (cell, code), n in visits.items() if cell >= 0)

    old = load(OUT, {})
    if old.get("places") == places and old.get("countries") == countries:
        print("no change:", len(places), "places in", len(countries), "countries")
        return
    dump(OUT, {"updated": datetime.date.today().isoformat(), "total": sum(visits.values()),
               "countries": countries, "places": places})
    print(len(places), "places in", len(countries), "countries,", sum(visits.values()), "visits;",
          len(live), "places from live counters")


if __name__ == "__main__":
    main()
