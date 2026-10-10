import unittest
from datetime import date
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

import main
from scrapers.base import RankItem


class ForceFetchTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"supabase": {"url": "test", "key": "test"},
                    "general": {"top_n": 20}, "platforms": {}}
        self.items = [RankItem(1, "真实游戏", "kuaibao", rank_type, game_id="123")
                      for rank_type in ("active", "download", "reservation")]
        self.scraper = Mock()
        self.scraper.SUPPORTED_RANK_TYPES = ["active", "download", "reservation"]
        self.scraper.fetch_all.return_value = self.items
        self.scraper_class = Mock(return_value=self.scraper)
        self.database = Mock()
        self.database.query.return_value = [{"platform": "kuaibao"}, {"platform": "taptap"}]
        self.db_patch = patch("storage.Database", return_value=self.database)
        self.registry_patch = patch("scrapers.ALL_SCRAPERS", {"kuaibao": self.scraper_class, "taptap": Mock()})
        self.db_patch.start()
        self.registry_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.registry_patch.stop)

    def test_normal_fetch_still_skips_existing_data(self):
        self.assertEqual(main.run_fetch(self.cfg, "kuaibao"), [])
        self.scraper_class.assert_not_called()
        self.database.delete_by_date.assert_not_called()

    def test_force_replaces_only_selected_platform_today(self):
        self.assertEqual(main.run_fetch(self.cfg, "kuaibao", force=True), self.items)
        self.database.delete_by_date.assert_called_once_with(date.today().isoformat(), platform="kuaibao")
        self.database.save.assert_called_once_with(self.items)

    def test_force_partial_failure_preserves_existing_data(self):
        self.scraper.fetch_all.return_value = self.items[:2]
        with self.assertRaisesRegex(click.ClickException, "reservation"):
            main.run_fetch(self.cfg, "kuaibao", force=True)
        self.database.delete_by_date.assert_not_called()
        self.database.save.assert_not_called()

    def test_force_requires_a_valid_explicit_platform(self):
        for platform in (None, "unknown"):
            with self.subTest(platform=platform), self.assertRaises(click.ClickException):
                main.run_fetch(self.cfg, platform, force=True)
        self.database.delete_by_date.assert_not_called()

    def test_cli_forwards_force_option(self):
        with patch.object(main, "load_config", return_value=self.cfg), \
             patch.object(main, "setup_logging"), patch.object(main, "run_fetch", return_value=[]) as fetch:
            result = CliRunner().invoke(main.cli, ["fetch", "--platform", "kuaibao", "--force"])
        self.assertEqual(result.exit_code, 0, result.output)
        fetch.assert_called_once_with(self.cfg, "kuaibao", force=True)


if __name__ == "__main__":
    unittest.main()
