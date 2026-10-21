"""Exercise plotResults.main without running benchmarks or rendering PNGs."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
import buildDashboard as dashboard

try:
    import plotResults
except ImportError:
    plotResults = None


@unittest.skipIf(plotResults is None, "The optional PNG plotting dependencies are unavailable")
class PlotDashboardIntegrationTests(unittest.TestCase):
    def exerciseMain(self, hasResults):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / "charts" / "dashboard.html"
            events = []

            def buildFixtureDashboard():
                events.append("dashboard")
                return dashboard.buildDashboard(directory / "results", output)

            frame = plotResults.pd.DataFrame({"algorithm": ["MergeSort"]}) if hasResults else plotResults.pd.DataFrame()

            def loadFixtureResults():
                events.append("loadResults")
                return frame

            with (patch.object(plotResults, "PROJECT_DIR", directory),
                  patch.object(plotResults, "buildDashboard", side_effect=buildFixtureDashboard) as build,
                  patch.object(plotResults, "loadResults", side_effect=loadFixtureResults),
                  patch.object(plotResults, "setTheme") as theme,
                  patch.object(plotResults, "plotGrowth") as growth,
                  patch.object(plotResults, "plotVariants") as variants,
                  patch.object(plotResults, "plotLanguages") as languages,
                  contextlib.redirect_stdout(io.StringIO()) as captured):
                plotResults.main()
                build.assert_called_once_with()
                theme.assert_called_once_with()
                self.assertEqual(events, ["dashboard", "loadResults"])
                self.assertTrue(output.is_file())
                self.assertNotIn("__DASHBOARD_PAYLOAD__", output.read_text(encoding="utf-8"))
                self.assertEqual(list(directory.rglob("*.png")), [])
                self.assertEqual(list(directory.rglob("*.csv")), [])
                if hasResults:
                    self.assertEqual(growth.call_args_list, [call(frame, "C++"), call(frame, "Python")])
                    self.assertEqual(variants.call_args_list, [
                        call(frame, 1000, 3), call(frame, 10000, 4), call(frame, 100000, 5),
                    ])
                    languages.assert_called_once_with(frame)
                else:
                    growth.assert_not_called()
                    variants.assert_not_called()
                    languages.assert_not_called()
                    self.assertIn("No measured or estimated results", captured.getvalue())

    def testDashboardIsBuiltEvenWhenResultsAreEmpty(self):
        self.exerciseMain(False)

    def testDashboardIsBuiltBeforeTheSixExistingChartCalls(self):
        self.exerciseMain(True)


if __name__ == "__main__":
    unittest.main()
