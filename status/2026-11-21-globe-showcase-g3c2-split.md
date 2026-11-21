# 2026-11-21 · globe-showcase · G3c2 split

**Step:** G3c2 (transform offset markers) is too large for one run, so it is split under the owner's 2026-10-21 rule. No code changed in this run.

**Finding:** `prototype/assets/plates/topologies.json` lists each feature as a type index and its coordinates. Transform features carry no plate IDs, so the two plates on either side of a transform cannot be read from that file. They can be found from `muller2019.json`, whose polygons carry plate IDs and age ranges (`from`, `to`). That lookup is G3c2a.

**Commands run:** `python3 -c` read of the topologies file header and one frame (structure only). No tests were needed: nothing under `prototype/`, `scripts/` or `tests/` changed.

**Next action:** G3c2a next run: write the side lookup as a script with a unit test on San Andreas. Owner: no decision needed.
