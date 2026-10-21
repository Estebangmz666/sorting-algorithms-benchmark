"""Isolated tests for dashboard ingestion; never use the running suite's CSVs."""

import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
import buildDashboard as dashboard


def resultRow(**changes):
    row = dict.fromkeys(dashboard.FIELDS, "")
    row.update({
        "algorithm": "MergeSort", "language": "cpp", "variant": "random", "n": "1000",
        "average_ms": "1.5", "stdDev_ms": "0.1", "status": "measured",
        "method": "five_executions", "growth_model": "nlogn",
        "repeat1_ms": "1.4", "repeat2_ms": "1.6",
    })
    row.update(changes)
    return row


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.template = self.directory / "template.html"
        self.template.write_text(
            '<!doctype html><script type="application/json" id="data">'
            '__DASHBOARD_PAYLOAD__</script>', encoding="utf-8",
        )

    def writeSource(self, rows, filename="results_cpp.csv", fields=None):
        path = self.directory / filename
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields or dashboard.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def testMissingSourcesRemainPendingAndLegacyIsIgnored(self):
        self.writeSource([resultRow()], "sorting_results.csv")
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(payload["rows"], [])
        self.assertEqual(payload["expectedCount"], 144)
        self.assertEqual(len(payload["warnings"]), 2)
        self.assertTrue(all(not source["exists"] for source in payload["sources"]))
        self.assertTrue(all(source["modifiedAt"] is None for source in payload["sources"]))
        self.assertIsNotNone(datetime.fromisoformat(payload["generatedAt"]).tzinfo)

    def testMeasuredFailedAndEstimatedHaveDistinctMissingValues(self):
        self.writeSource([
            resultRow(),
            resultRow(n="10000", average_ms="", stdDev_ms="", status="failed",
                      repeat1_ms="", repeat2_ms="", error="Time limit exceeded"),
            resultRow(n="100000", average_ms="1500", stdDev_ms="", status="estimated",
                      method="theoretical_extrapolation", reference_n="1000",
                      reference_average_ms="1.5", repeat1_ms="", repeat2_ms=""),
        ])
        rows = dashboard.collectPayload(self.directory)["rows"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["repetitions_ms"], [1.4, 1.6])
        self.assertIsNone(rows[1]["average_ms"])
        self.assertIsNone(rows[1]["stdDev_ms"])
        self.assertEqual(rows[1]["repetitions_ms"], [])
        self.assertIsNone(rows[0]["reference_n"])
        self.assertEqual(rows[2]["reference_n"], 1000)
        self.assertEqual(rows[2]["reference_average_ms"], 1.5)

    def testLanguageComesFromCanonicalFileAndAliasesAreAccepted(self):
        self.writeSource([resultRow(language="C++")])
        self.writeSource([resultRow(language="Python")], "results_py.csv")
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual([row["language"] for row in payload["rows"]], ["cpp", "py"])
        self.assertEqual([source["rowCount"] for source in payload["sources"]], [1, 1])

    def testMismatchedLanguageIsRejected(self):
        self.writeSource([resultRow(language="py")])
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(payload["rows"], [])
        self.assertTrue(any("lenguaje" in warning for warning in payload["warnings"]))

    def testFailedRowNeverExposesAnAggregateTime(self):
        self.writeSource([resultRow(status="failed", average_ms="1.5", error="Interrupted")])
        row = dashboard.collectPayload(self.directory)["rows"][0]
        self.assertIsNone(row["average_ms"])
        self.assertEqual(row["repetitions_ms"], [1.4, 1.6])

    def testDecimalAndScientificNotationAreAcceptedWithoutInventingRepetitions(self):
        self.writeSource([resultRow(n="+1e3", average_ms=".15e+1", repeat1_ms="", repeat2_ms="")])
        row = dashboard.collectPayload(self.directory)["rows"][0]
        self.assertEqual(row["n"], 1000)
        self.assertEqual(row["average_ms"], 1.5)
        self.assertEqual(row["repetitions_ms"], [])

    def testUnknownKeysAndInvalidNumericsAreRejected(self):
        invalidChanges = [
            {"algorithm": "UnknownSort"}, {"variant": "unknown"}, {"n": "2000"},
            {"n": "-1000"}, {"n": "nan"}, {"n": ""}, {"status": "pending"},
            {"average_ms": "inf"}, {"average_ms": "NaN"}, {"average_ms": "-2"},
            {"average_ms": "0"}, {"average_ms": ""}, {"average_ms": "oops"},
            {"stdDev_ms": "-1"}, {"stdDev_ms": "inf"}, {"repeat1_ms": "-1"},
            {"n": "1_000"}, {"n": "0x3e8"}, {"n": "١٠٠٠"},
            {"average_ms": "0x10"}, {"average_ms": "1_000"},
            {"reference_n": "1000"}, {"reference_average_ms": "1"},
            {"reference_n": "1000", "reference_average_ms": "1"},
            {"growth_model": "invented"},
        ]
        self.writeSource([resultRow(**changes) for changes in invalidChanges])
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(payload["rows"], [])
        self.assertEqual(sum("fila omitida" in warning for warning in payload["warnings"]),
                         len(invalidChanges))

    def testLastValidDuplicateWinsAndInvalidDuplicateDoesNotEraseIt(self):
        self.writeSource([
            resultRow(average_ms="1"), resultRow(average_ms="2"), resultRow(average_ms="NaN"),
        ])
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(len(payload["rows"]), 1)
        self.assertEqual(payload["rows"][0]["average_ms"], 2)
        self.assertEqual(payload["sources"][0]["rowCount"], 1)
        self.assertTrue(any("duplicada" in warning for warning in payload["warnings"]))

    def testMissingBasicColumnsRejectsSource(self):
        self.writeSource([{"algorithm": "MergeSort"}], fields=["algorithm"])
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(payload["rows"], [])
        self.assertTrue(payload["sources"][0]["exists"])
        self.assertTrue(any("columnas básicas" in warning for warning in payload["warnings"]))

    def testDuplicateHeadersRejectsSource(self):
        (self.directory / "results_cpp.csv").write_text(
            "algorithm,algorithm,language,variant,n,average_ms,status\n"
            "MergeSort,MergeSort,cpp,random,1000,1,measured\n", encoding="utf-8",
        )
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(payload["rows"], [])
        self.assertTrue(any("columnas duplicadas" in warning for warning in payload["warnings"]))

    def testAdditionalColumnsWarnButDoNotInvalidateValidData(self):
        self.writeSource([dict(resultRow(), comment="extra")], fields=dashboard.FIELDS + ["comment"])
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(len(payload["rows"]), 1)
        self.assertTrue(any("columnas desconocidas" in warning for warning in payload["warnings"]))

    def testMalformedTrailingCSVPreservesEarlierRows(self):
        path = self.writeSource([resultRow()])
        with path.open("a", encoding="utf-8") as file:
            file.write('"unterminated')
        payload = dashboard.collectPayload(self.directory)
        self.assertEqual(len(payload["rows"]), 1)
        self.assertTrue(any("mal formado" in warning for warning in payload["warnings"]))

    def testUnsafeScriptTextIsEscapedAndJsonRoundTrips(self):
        unsafeText = '</script><script>alert("x")</script> & \u2028 \u2029 café'
        payload = {"error": unsafeText}
        serialized = dashboard.serializePayload(payload)
        self.assertNotIn("<", serialized)
        self.assertNotIn("\u2028", serialized)
        self.assertNotIn("\u2029", serialized)
        self.assertEqual(json.loads(serialized), payload)
        self.writeSource([resultRow(error=unsafeText, method=unsafeText)])
        output = dashboard.buildDashboard(self.directory, self.directory / "out.html", self.template)
        html = output.read_text(encoding="utf-8")
        self.assertEqual(html.count("</script>"), 1)
        self.assertNotIn("__DASHBOARD_PAYLOAD__", html)

    def testBuildDoesNotChangeSourcesAndSupportsNoResults(self):
        path = self.writeSource([resultRow()])
        before = path.read_bytes()
        output = self.directory / "charts" / "dashboard.html"
        self.assertEqual(dashboard.buildDashboard(self.directory, output, self.template), output.resolve())
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(output.parent.glob("*.tmp")), [])
        emptyOutput = self.directory / "empty.html"
        dashboard.buildDashboard(self.directory / "nonexistent", emptyOutput, self.template)
        self.assertTrue(emptyOutput.is_file())

    def testFailedAtomicReplacePreservesPreviousOutputAndCleansTemporary(self):
        output = self.directory / "out.html"
        output.write_text("previous", encoding="utf-8")
        with patch.object(Path, "replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                dashboard.buildDashboard(self.directory, output, self.template)
        self.assertEqual(output.read_text(encoding="utf-8"), "previous")
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def testInvalidMarkerCountAndInputOutputCollisionAreRejected(self):
        self.template.write_text("__DASHBOARD_PAYLOAD__ __DASHBOARD_PAYLOAD__", encoding="utf-8")
        with self.assertRaises(ValueError):
            dashboard.buildDashboard(self.directory, self.directory / "out.html", self.template)
        self.template.write_text("__DASHBOARD_PAYLOAD__", encoding="utf-8")
        with self.assertRaises(ValueError):
            dashboard.buildDashboard(self.directory, self.template, self.template)
        source = self.writeSource([resultRow()])
        with self.assertRaises(ValueError):
            dashboard.buildDashboard(self.directory, source, self.template)


if __name__ == "__main__":
    unittest.main()
