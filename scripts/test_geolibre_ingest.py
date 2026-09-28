import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geolibre_ingest as gi  # noqa: E402

SON = [-122.52, 38.30]            # inside the Sonoma Valley frame
FAR = [-120.0, 36.0]              # well outside it


def poly(c, props=None):
    x, y = c
    return {"type": "Feature", "properties": props or {},
            "geometry": {"type": "Polygon", "coordinates": [[[x, y], [x + .01, y], [x + .01, y + .01], [x, y]]]}}


def lyr(name, feats, **extra):
    return {"id": name, "name": name, "type": "geojson", "source": {"type": "geojson"}, "visible": True,
            "opacity": 1, "style": {}, "metadata": {}, "geojson": {"type": "FeatureCollection", "features": feats}, **extra}


class VerdictTest(unittest.TestCase):
    def test_allowed_hosts_are_accepted(self):
        for u in ("https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest",
                  "https://services.conservation.ca.gov/arcgis/rest/services/CGS/Geologic_Map/MapServer/0",
                  "https://index.nationalmap.gov/arcgis/rest/services/x/MapServer",
                  "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/x.geojson"):
            self.assertEqual(gi.verdict("soils: x", [u])[0], "accepted", u)

    def test_blocked_sources_are_rejected(self):
        self.assertEqual(gi.verdict("x", ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"])[0], "rejected")
        self.assertEqual(gi.verdict("places: county parcels", ["https://gis.napa.ca.gov/x"])[1], "parcel data")
        self.assertEqual(gi.verdict("soils: x", ["https://sdmdataaccess.nrcs.usda.gov/q?token=abc"])[1], "URL carries a key or token")

    def test_lookalike_hosts_and_unknown_hosts_need_review(self):
        self.assertEqual(gi.verdict("x", ["https://usgs.gov.evil.example/x"])[0], "needs_review")
        self.assertEqual(gi.verdict("x", ["https://services3.arcgis.com/abc/FeatureServer/0"])[0], "needs_review")
        self.assertEqual(gi.verdict("x", [])[0], "needs_review")

    def test_owner_can_accept_but_not_unblock(self):
        u = "https://services3.arcgis.com/abc/FeatureServer/0"
        self.assertEqual(gi.verdict("x", [u], {"owner_accepted": True})[0], "accepted")
        self.assertEqual(gi.verdict("x", ["https://server.arcgisonline.com/x"], {"owner_accepted": True})[0], "rejected")

    def test_urls_found_in_source_and_metadata_not_features(self):
        l = lyr("soils: a", [poly(SON, {"link": "https://ignored.example/"})], sourcePath="https://a.usgs.gov/x",
                metadata={"femaWmsUrl": "https://b.ca.gov/y"})
        self.assertEqual(gi.layer_urls(l), ["https://a.usgs.gov/x", "https://b.ca.gov/y"])

    def test_role_prefix(self):
        self.assertEqual(gi.role_of("Soils : SSURGO"), ("soils", "SSURGO"))
        self.assertEqual(gi.role_of("Sonoma Valley AVA")[0], None)
        self.assertEqual(gi.role_of("roads: x")[0], None)


class IngestTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "data" / "geolibre").mkdir(parents=True)
        (self.root / "data" / "manifest.json").write_text(json.dumps({"datasets": [{"id": "keep-me"}]}))
        self.proj = self.root / "data" / "geolibre" / "sonoma_valley.geolibre"
        self.proj.write_text(json.dumps({"version": "0.1.0", "name": "t", "mapView": {}, "layers": [
            lyr("Sonoma Valley AVA", [poly(SON)]),
            lyr("soils: SSURGO map units", [poly(SON), poly(FAR), {"type": "Feature", "properties": {},
                "geometry": {"type": "Point", "coordinates": SON}}], sourcePath="https://sdmdataaccess.nrcs.usda.gov/x"),
            lyr("geology: some county layer", [poly(SON)], sourcePath="https://services3.arcgis.com/abc/FeatureServer/0"),
            lyr("vineyards: imagery trace", [poly(SON)], source={"type": "raster", "tiles": ["https://server.arcgisonline.com/World_Imagery/{z}"]}),
            lyr("faults: linked only", [], sourcePath="https://earthquake.usgs.gov/x"),
        ]}))

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_verdicts_outputs_and_manifest(self):
        r = gi.ingest(self.proj, root=self.root)
        got = {row["role"]: row["status"] for row in r["layers"]}
        self.assertEqual(got, {"soils": "accepted", "geology": "needs_review", "vineyards": "rejected", "faults": "needs_review"})
        soils = next(row for row in r["layers"] if row["role"] == "soils")
        self.assertEqual((soils["kept"], soils["wrong_geometry"]), (1, 1))
        out = json.loads((self.root / "data" / "intake" / "sonoma_valley" / "soils.geojson").read_text())
        self.assertEqual(len(out["features"]), 1)
        self.assertFalse((self.root / "data" / "intake" / "sonoma_valley" / "geology.geojson").exists())
        man = json.loads((self.root / "data" / "manifest.json").read_text())["datasets"]
        self.assertEqual([d["id"] for d in man], ["keep-me", "geolibre-sonoma_valley-soils"])
        self.assertEqual(man[1]["status"], "pending_verification")
        self.assertEqual(man[1]["rights"], "unverified")
        gi.ingest(self.proj, root=self.root)          # re-import replaces, not duplicates
        self.assertEqual(len(json.loads((self.root / "data" / "manifest.json").read_text())["datasets"]), 2)

    def test_sources_file_lets_the_owner_accept(self):
        (self.root / "data" / "geolibre" / "sonoma_valley.sources.json").write_text(json.dumps(
            {"geology: some county layer": {"owner_accepted": True, "licence": "public domain"}}))
        r = gi.ingest(self.proj, root=self.root)
        self.assertEqual(next(row for row in r["layers"] if row["role"] == "geology")["status"], "accepted")
        man = json.loads((self.root / "data" / "manifest.json").read_text())["datasets"]
        self.assertEqual(next(d for d in man if d["id"].endswith("geology"))["rights"], "public domain")

    def test_dry_run_writes_nothing(self):
        gi.ingest(self.proj, dry_run=True, root=self.root)
        self.assertFalse((self.root / "data" / "intake").exists())

    def test_rejects_non_projects_and_bad_names(self):
        bad = self.root / "data" / "geolibre" / "x.geolibre"
        bad.write_text("{}")
        with self.assertRaises(SystemExit):
            gi.ingest(bad, root=self.root)
        odd = self.root / "data" / "geolibre" / "Bad Name.geolibre"
        odd.write_text(self.proj.read_text())
        with self.assertRaises(SystemExit):
            gi.ingest(odd, root=self.root)


if __name__ == "__main__":
    unittest.main()
