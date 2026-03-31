import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import unreal_cli


class UnrealCliTests(unittest.TestCase):
    def test_root_help_mentions_castle_commands(self):
        parser = unreal_cli.build_parser()
        buffer = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(buffer):
            parser.parse_args(["--help"])
        output = buffer.getvalue()
        self.assertIn("create-basic-castle", output)
        self.assertIn("verify-basic-castle", output)
        self.assertIn("reset-basic-castle", output)
        self.assertIn("remote-call", output)

    def test_commands_lists_expected_entries(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main(["commands"])
        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("create-basic-castle", output)
        self.assertIn("list-level-actors", output)

    def test_create_basic_castle_dry_run_returns_plan(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main(["create-basic-castle", "--prefix", "SpecCastle", "--dry-run"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["prefix"], "SpecCastle")
        self.assertEqual(payload["variation"]["layout"], "classic")
        self.assertEqual(payload["actor_count"], 16)

    @patch("unreal_mcp.cli.verify_basic_castle")
    def test_verify_basic_castle_command_routes_result(self, verify_basic_castle_mock):
        verify_basic_castle_mock.return_value = json.dumps({"is_complete": True})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main(["verify-basic-castle", "--prefix", "SkillCastle"])
        self.assertEqual(exit_code, 0)
        verify_basic_castle_mock.assert_called_once_with("SkillCastle")
        self.assertIn("is_complete", buffer.getvalue())

    @patch("unreal_mcp.cli.create_basic_castle")
    def test_create_basic_castle_defaults_to_replacement(self, create_basic_castle_mock):
        create_basic_castle_mock.return_value = json.dumps({"created_count": 16})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main(["create-basic-castle", "--prefix", "SkillCastle"])
        self.assertEqual(exit_code, 0)
        create_basic_castle_mock.assert_called_once_with(
            "SkillCastle",
            [0.0, 0.0, 0.0],
            None,
            None,
            False,
            True,
            "classic",
            "standard",
            "granite",
            0.0,
        )
        self.assertIn("created_count", buffer.getvalue())

    @patch("unreal_mcp.cli.create_basic_castle")
    def test_create_basic_castle_routes_variation_flags(self, create_basic_castle_mock):
        create_basic_castle_mock.return_value = json.dumps({"created_count": 16})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main([
                "create-basic-castle",
                "--prefix", "VariantCastle",
                "--layout", "courtyard",
                "--size", "grand",
                "--palette", "sandstone",
                "--yaw", "45",
            ])
        self.assertEqual(exit_code, 0)
        create_basic_castle_mock.assert_called_once_with(
            "VariantCastle",
            [0.0, 0.0, 0.0],
            None,
            None,
            False,
            True,
            "courtyard",
            "grand",
            "sandstone",
            45.0,
        )

    @patch("unreal_mcp.cli.reset_basic_castle")
    def test_reset_basic_castle_command_routes_result(self, reset_basic_castle_mock):
        reset_basic_castle_mock.return_value = json.dumps({"delete_count": 2})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = unreal_cli.main(["reset-basic-castle", "--prefix", "SkillCastle", "--strict-plan"])
        self.assertEqual(exit_code, 0)
        reset_basic_castle_mock.assert_called_once_with("SkillCastle", True, False)
        self.assertIn("delete_count", buffer.getvalue())