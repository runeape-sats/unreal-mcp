import json
import unittest
from unittest.mock import patch

from examples.castle.workflow import build_castle_instances, reset_basic_castle, verify_basic_castle


class CastleWorkflowTests(unittest.TestCase):
    def test_build_castle_instances_applies_prefix_and_origin(self):
        instances = build_castle_instances(prefix="SkillCastle", origin=[100.0, 200.0, 300.0])
        self.assertEqual(instances[0]["actor_label"], "SkillCastle_Keep")
        self.assertEqual(instances[0]["location"], [100.0, 200.0, 540.0])

    def test_build_castle_instances_supports_variation_presets(self):
        instances = build_castle_instances(
            prefix="VariantCastle",
            layout="bastion",
            size="grand",
            palette="obsidian",
            yaw=90.0,
        )
        keep = next(instance for instance in instances if instance["actor_label"] == "VariantCastle_Keep")
        gatehouse = next(instance for instance in instances if instance["actor_label"] == "VariantCastle_Gatehouse")
        roof_keep = next(instance for instance in instances if instance["actor_label"] == "VariantCastle_RoofKeep")

        self.assertEqual(keep["color"], [0.18, 0.2, 0.25])
        self.assertEqual(roof_keep["color"], [0.48, 0.12, 0.1])
        self.assertEqual(keep["rotation"], [0.0, 90.0, 0.0])
        self.assertAlmostEqual(gatehouse["location"][0], 1548.96, places=2)
        self.assertAlmostEqual(gatehouse["location"][1], 0.0, places=2)

    def test_build_castle_instances_rejects_unknown_layout(self):
        with self.assertRaises(ValueError):
            build_castle_instances(layout="unknown")

    @patch("examples.castle.workflow.list_level_actors")
    def test_verify_basic_castle_detects_missing_actors(self, list_level_actors_mock):
        list_level_actors_mock.return_value = json.dumps({
            "actors": [
                {"label": "SkillCastle_Keep"},
                {"label": "SkillCastle_Gatehouse"}
            ]
        })
        result = json.loads(verify_basic_castle("SkillCastle"))
        self.assertFalse(result["is_complete"])
        self.assertIn("SkillCastle_WallNorth", result["missing"])

    @patch("examples.castle.workflow.list_level_actors")
    def test_verify_basic_castle_accepts_complete_castle(self, list_level_actors_mock):
        found = [{"label": instance["actor_label"]} for instance in build_castle_instances("SkillCastle")]
        list_level_actors_mock.return_value = json.dumps({"actors": found})
        result = json.loads(verify_basic_castle("SkillCastle"))
        self.assertTrue(result["is_complete"])
        self.assertEqual(result["matched_count"], 16)

    @patch("examples.castle.workflow.delete_actor")
    @patch("examples.castle.workflow.list_level_actors")
    def test_reset_basic_castle_deletes_matching_prefix(self, list_level_actors_mock, delete_actor_mock):
        list_level_actors_mock.return_value = json.dumps({
            "actors": [
                {"label": "SkillCastle_Keep"},
                {"label": "SkillCastle_RoofKeep"},
                {"label": "SkillCastle_Custom"}
            ]
        })
        delete_actor_mock.return_value = "Successfully deleted actor 'SkillCastle_Keep'"

        result = json.loads(reset_basic_castle("SkillCastle"))
        self.assertEqual(result["delete_count"], 3)
        self.assertEqual(delete_actor_mock.call_count, 3)

    @patch("examples.castle.workflow.list_level_actors")
    def test_reset_basic_castle_strict_plan_filters_custom_labels(self, list_level_actors_mock):
        list_level_actors_mock.return_value = json.dumps({
            "actors": [
                {"label": "SkillCastle_Keep"},
                {"label": "SkillCastle_Custom"}
            ]
        })
        result = json.loads(reset_basic_castle("SkillCastle", strict_plan=True, dry_run=True))
        self.assertEqual(result["delete_count"], 1)
        self.assertEqual(result["targets"], ["SkillCastle_Keep"])