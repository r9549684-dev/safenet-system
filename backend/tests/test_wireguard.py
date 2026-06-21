"""Tests for WireGuardService._stealth_params — AWG 1.x vs 2.0 version branching."""
import os
import sys
import re
import unittest
from unittest.mock import MagicMock

# Backend в sys.path
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.services.wireguard import WireGuardService, AWG_STEALTH_DEFAULTS


def _make_server(meta: dict | None) -> MagicMock:
    srv = MagicMock()
    srv.meta = meta if meta is not None else {}
    return srv


class TestStealthParamsV1(unittest.TestCase):
    """AWG 1.x — классический формат (backward-compatible)."""

    def test_v1_explicit(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 1}))
        self.assertEqual(
            set(params.keys()),
            {"Jc", "Jmin", "Jmax", "S1", "S2", "H1", "H2", "H3", "H4"},
        )

    def test_v1_default_when_meta_empty(self):
        # awg_version отсутствует → v1 by default
        params = WireGuardService._stealth_params(_make_server({}))
        self.assertEqual(
            set(params.keys()),
            {"Jc", "Jmin", "Jmax", "S1", "S2", "H1", "H2", "H3", "H4"},
        )

    def test_v1_default_when_meta_none(self):
        params = WireGuardService._stealth_params(_make_server(None))
        self.assertEqual(
            set(params.keys()),
            {"Jc", "Jmin", "Jmax", "S1", "S2", "H1", "H2", "H3", "H4"},
        )

    def test_v1_no_v2_params(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 1}))
        for key in ("S3", "S4", "I1", "I2", "I3", "I4", "I5"):
            self.assertNotIn(key, params, f"v1 must NOT contain '{key}'")

    def test_v1_h_values_are_integers(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 1}))
        for k in ("H1", "H2", "H3", "H4"):
            self.assertIsInstance(params[k], int)
            self.assertGreaterEqual(params[k], 1)

    def test_v1_jmin_less_than_jmax(self):
        for _ in range(20):
            params = WireGuardService._stealth_params(_make_server({}))
            self.assertLess(params["Jmin"], params["Jmax"])
            self.assertGreaterEqual(params["Jmax"] - params["Jmin"], 5)

    def test_v1_server_stealth_overrides_defaults(self):
        srv = _make_server({
            "awg_version": 1,
            "stealth": {"Jc": 7, "Jmin": 10, "Jmax": 20, "S1": 80, "S2": 40},
        })
        params = WireGuardService._stealth_params(srv)
        self.assertEqual(params["Jc"], 7)
        self.assertEqual(params["S1"], 80)
        self.assertEqual(params["S2"], 40)


class TestStealthParamsV2(unittest.TestCase):
    """AWG 2.0 — новый формат (+ S3/S4, + I1-I5, H-ranges)."""

    def test_v2_has_v1_params(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 2}))
        for key in ("Jc", "Jmin", "Jmax", "S1", "S2"):
            self.assertIn(key, params)

    def test_v2_has_s3_s4(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 2}))
        self.assertIn("S3", params)
        self.assertIn("S4", params)

    def test_v2_has_special_junk_strings(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 2}))
        for key in ("I1", "I2", "I3", "I4", "I5"):
            self.assertIn(key, params)
            self.assertIsInstance(params[key], str)
            # secrets.token_hex produces even-length hex
            self.assertGreater(len(params[key]), 0)

    def test_v2_i_strings_differ_between_calls(self):
        srv = _make_server({"awg_version": 2})
        p1 = WireGuardService._stealth_params(srv)
        # Статистически: 5 вызовов — крайне маловероятно что все совпадут
        p2 = WireGuardService._stealth_params(srv)
        differ = any(p1[k] != p2[k] for k in ("I1", "I2", "I3", "I4", "I5"))
        self.assertTrue(differ, "I-strings should differ between calls")

    def test_v2_h_values_are_range_strings(self):
        params = WireGuardService._stealth_params(_make_server({"awg_version": 2}))
        for k in ("H1", "H2", "H3", "H4"):
            self.assertIsInstance(params[k], str)
            self.assertRegex(params[k], r"^\d+-\d+$")
            lo, hi = [int(x) for x in params[k].split("-")]
            self.assertGreater(hi, lo)

    def test_v2_h_ranges_valid_for_different_lengths(self):
        # H3/H4 — короткие диапазоны (1-20..21-45); H1/H2 — широкие.
        for _ in range(10):
            params = WireGuardService._stealth_params(_make_server({"awg_version": 2}))
            for k in ("H1", "H2"):
                lo, hi = [int(x) for x in params[k].split("-")]
                self.assertGreater(lo, 0)
                self.assertGreater(hi, lo)
            for k in ("H3", "H4"):
                lo, hi = [int(x) for x in params[k].split("-")]
                self.assertGreaterEqual(lo, 1)
                self.assertLessEqual(hi, 45)

    def test_v2_s3_s4_from_server_meta(self):
        srv = _make_server({
            "awg_version": 2,
            "stealth": {
                "Jc": 4, "Jmin": 12, "Jmax": 22, "S1": 60, "S2": 30,
                "S3": 42, "S4": 18,
            },
        })
        params = WireGuardService._stealth_params(srv)
        self.assertEqual(params["S3"], 42)
        self.assertEqual(params["S4"], 18)

    def test_v2_s3_s4_default_when_not_in_meta(self):
        # stealth field present but no S3/S4 — use AWG_STEALTH_DEFAULTS
        srv = _make_server({
            "awg_version": 2,
            "stealth": {"Jc": 5, "Jmin": 14, "Jmax": 24, "S1": 65, "S2": 35},
        })
        params = WireGuardService._stealth_params(srv)
        self.assertEqual(params["S3"], AWG_STEALTH_DEFAULTS["S3"])  # 0
        self.assertEqual(params["S4"], AWG_STEALTH_DEFAULTS["S4"])  # 0

    def test_v2_i_strings_from_server_meta_override(self):
        fixed_strings = {"I1": "deadbeef", "I2": "cafebabe", "I3": "0123456789abcdef",
                         "I4": "aabb", "I5": "ccdd"}
        srv = _make_server({
            "awg_version": 2,
            "stealth": {
                "Jc": 3, "Jmin": 15, "Jmax": 20, "S1": 55, "S2": 25,
                **fixed_strings,
            },
        })
        params = WireGuardService._stealth_params(srv)
        for k, v in fixed_strings.items():
            self.assertEqual(params[k], v)


class TestGenerateConfigAWGVersion(unittest.TestCase):
    """generate_wg_config: stealth-block отражает версию AWG."""

    def _server(self, awg_version: int | None, **extra_meta) -> MagicMock:
        meta: dict = {}
        if awg_version is not None:
            meta["awg_version"] = awg_version
        if extra_meta:
            meta.update(extra_meta)
        meta.setdefault("wg_public_key", "TEST_PUBKEY=")
        meta.setdefault("wg_port", 51820)
        srv = MagicMock()
        srv.meta = meta
        srv.host = "198.51.100.10"
        srv.port = 51820
        return srv

    def test_v1_config_no_v2_lines(self):
        config = WireGuardService.generate_wg_config(self._server(1), "KEY=", "10.8.0.5")
        for key in ("S3", "S4", "I1", "I2", "I3", "I4", "I5"):
            self.assertNotIn(f"{key} =", config,
                             f"v1 config must not contain '{key} ='")

    def test_v2_config_has_v2_params(self):
        config = WireGuardService.generate_wg_config(self._server(2), "KEY=", "10.8.0.5")
        for key in ("S3", "S4", "I1", "I2", "I3", "I4", "I5"):
            self.assertIn(f"{key} =", config,
                          f"v2 config must contain '{key} ='")

    def test_v2_h_ranges_appear_as_strings_in_config(self):
        config = WireGuardService.generate_wg_config(self._server(2), "KEY=", "10.8.0.5")
        for k in ("H1", "H2", "H3", "H4"):
            match = re.search(rf"^{k} = (.+)$", config, re.MULTILINE)
            self.assertIsNotNone(match, f"Config must contain '{k} ='")
            self.assertRegex(match.group(1), r"^\d+-\d+$",
                             f"H-value for {k} must be 'min-max' string")

    def test_v1_h_values_are_bare_integers(self):
        config = WireGuardService.generate_wg_config(self._server(1), "KEY=", "10.8.0.5")
        for k in ("H1", "H2", "H3", "H4"):
            match = re.search(rf"^{k} = (.+)$", config, re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertTrue(match.group(1).isdigit(),
                            f"H for {k} must be bare int, got '{match.group(1)}'")


if __name__ == "__main__":
    unittest.main()
