import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("update_version", Path(__file__).with_name("update-version.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class UpdateVersionTest(unittest.TestCase):
    recipe = "name: piqueserver\nversion: '1.4.2'\nparts:\n  piqueserver:\n    source: https://github.com/piqueserver/piqueserver.git\n    source-tag: v1.4.2\n    build-environment:\n      - SETUPTOOLS_SCM_PRETEND_VERSION: \"$SNAPCRAFT_PROJECT_VERSION\"\n"

    def test_live_recipe_has_supported_consistent_identity(self):
        text = Path("snap/snapcraft.yaml").read_text()
        tag = module.re.search(r"(?m)^    source-tag: (.+)$", text)[1]
        self.assertEqual(module.update(text, tag, True), text)

    def test_coupled_update_preserves_rest_of_recipe(self):
        got = module.update(self.recipe, "v1.4.3")
        self.assertEqual(got, self.recipe.replace("version: '1.4.2'", "version: '1.4.3'").replace("source-tag: v1.4.2", "source-tag: v1.4.3"))
        self.assertEqual(module.update(got, "v1.4.3"), got)

    def test_current_tag_is_read_only(self):
        self.assertEqual(module.update(self.recipe, "v1.4.2", True), self.recipe)

    def test_rejects_invalid_downgrade_and_inconsistent_identity(self):
        for tag in ("v1.4.1", "v1.5.0-beta", "main", "v1.5.0\nversion: '1.5.0'"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                module.update(self.recipe, tag)
        for text in (self.recipe.replace("version: '1.4.2'", "version: '1.4.1'"), self.recipe + "\nversion: '1.4.2'\n", self.recipe + "\n    source-tag: v1.4.2\n"):
            with self.assertRaises(ValueError):
                module.update(text, "v1.4.3")


if __name__ == "__main__":
    unittest.main()
