import json
import re
import unittest
from pathlib import Path

from examples.castle import CASTLE_PLAN_PATH, load_castle_plan


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "examples" / "castle" / "specs" / "CastleConstruction.tla"
SKILL_PATH = ROOT / ".github" / "skills" / "unreal-castle-builder" / "SKILL.md"


class CastleAssetTests(unittest.TestCase):
    def test_castle_plan_has_unique_labels(self):
        plan = load_castle_plan()
        labels = [entry["label_suffix"] for entry in plan["actors"]]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(len(labels), 16)

    def test_tla_required_actors_match_castle_plan(self):
        plan = load_castle_plan()
        expected = {entry["label_suffix"] for entry in plan["actors"]}
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        match = re.search(r"RequiredActors == \{(?P<body>.*?)\}", spec_text, re.DOTALL)
        self.assertIsNotNone(match)
        body = match.group("body")
        actual = {label for label in re.findall(r'"([^"]+)"', body)}
        self.assertEqual(actual, expected)

    def test_skill_references_cli_and_verification(self):
        skill_text = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("unreal-mcp-cli --help", skill_text)
        self.assertIn("create-basic-castle", skill_text)
        self.assertIn("--layout", skill_text)
        self.assertIn("list-level-actors", skill_text)
        self.assertIn("verify-basic-castle", skill_text)
        self.assertIn("reset-basic-castle", skill_text)

    def test_castle_plan_is_json_serializable(self):
        raw = CASTLE_PLAN_PATH.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        self.assertIn("actors", parsed)
        self.assertGreater(len(parsed["actors"]), 0)

    def test_tla_model_mentions_retries_and_rebuild(self):
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        self.assertIn("RetryFailedActor", spec_text)
        self.assertIn("StartRebuild", spec_text)
        self.assertIn("RetriesBounded", spec_text)

    def test_tla_model_mentions_variants(self):
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        self.assertIn("LayoutVariants", spec_text)
        self.assertIn("SizeVariants", spec_text)
        self.assertIn("PaletteVariants", spec_text)
        self.assertIn("VariantPreservesCoreActors", spec_text)