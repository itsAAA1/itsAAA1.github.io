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

    def test_concurrent_clicks_and_direct_calls_are_guarded(self):
        self.run_scenario("concurrent-guard")

    def test_button_is_reenabled_after_success_and_all_failure_modes(self):
        self.run_scenario("button-finally")

    def test_partial_failure_aborts_pending_sibling_and_allows_recovery(self):
        self.run_scenario("partial-aborts-sibling")

    def test_timeout_aborts_both_reads_and_allows_recovery(self):
        self.run_scenario("timeout-recovery")


if __name__ == "__main__":
    unittest.main()
