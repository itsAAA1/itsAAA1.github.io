"""Offline behavioural regressions for the read-only balance display."""
from pathlib import Path
import subprocess
import unittest

FIXTURE = Path(__file__).with_name("wallet_refresh_fixture.js")


class WalletRefreshRegression(unittest.TestCase):
    def run_scenario(self, name):
        result = subprocess.run(
            ["node", str(FIXTURE), name], capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS " + name, result.stdout)

    def test_initial_failure_keeps_original_snapshot_source_and_date(self):
        self.run_scenario("initial-failure")

    def test_success_then_failure_keeps_last_success_source_time_and_values(self):
        self.run_scenario("success-failure")

    def test_partial_rpc_error_malformed_and_offline_keep_last_success(self):
        self.run_scenario("partial-and-invalid")

    def test_recovery_replaces_previous_success_only_after_both_reads_succeed(self):
        self.run_scenario("recovery")


if __name__ == "__main__":
    unittest.main()
