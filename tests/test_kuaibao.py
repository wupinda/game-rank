import unittest
from unittest.mock import Mock, patch

from scrapers.kuaibao import KuaibaoScraper


def card(rank, game_id, name="测试游戏"):
    return f'''<div class="game-item"><div class="item-num">{rank}</div>
      <div class="game-icon"><a href="//www.3839.com/a/{game_id}.htm">
      <img src="//img.71acg.net/icon.png"></a></div>
      <div class="game-name"><span class="sp-name">{name}</span></div>
      <div class="sp-score">8.6</div></div>'''


def response(text="", payload=None):
    result = Mock(text=text)
    result.json.return_value = payload
    return result


class KuaibaoTests(unittest.TestCase):
    def setUp(self):
        self.scraper = KuaibaoScraper()

    def test_navigation_is_not_a_game(self):
        html = '''<div class="rankWrap"><ul class="rank-menu">
          <li>热门榜</li><li>预约榜</li><li>开发者</li></ul>
          <ul class="lb-item"><li>综合</li><li>热度</li><li>最新</li></ul></div>'''
        self.assertEqual(self.scraper._parse_html(html, "reservation"), [])
        items = self.scraper._parse_html(html + card(1, 123, "极限战场"), "reservation")
        self.assertEqual([(i.rank, i.name, i.game_id) for i in items], [(1, "极限战场", "123")])
        self.assertEqual(items[0].rating, 8.6)
        self.assertEqual(items[0].icon_url, "https://img.71acg.net/icon.png")

    def test_requires_identity_and_rank_and_deduplicates_by_id(self):
        html = (card("广告", 1) + card(2, "not-a-game") + card(3, 123, "2048")
                + card(3, 123, "重复卡片") + card(4, 124, "2048"))
        items = self.scraper._parse_html(html, "reservation")
        self.assertEqual([(i.rank, i.game_id) for i in items], [(3, "123"), (4, "124")])

    def test_legacy_download_cards_exclude_nested_screenshots(self):
        html = '''<ul class="ranking-game ranking-list"><li class="rankli">
          <span class="rank-num">1</span><a href="/a/123.htm"><img class="gameLogo" src="//img.71acg.net/1.png"></a>
          <div class="gameInfo"><div class="name"><span class="sp-name">下载游戏</span></div>
          <p class="auth">厂商：<a>万代游戏</a></p><div class="gameScore"><span class="score">9.1分</span></div></div>
          <ul><li><a href="/a/999.htm">截图</a></li></ul></li></ul>'''
        items = self.scraper._parse_html(html, "download")
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0].name, items[0].developer, items[0].rating), ("下载游戏", "万代游戏", 9.1))

    def test_uses_pages_current_default_and_paginates(self):
        self.scraper.TOP_N = 3
        page = response("<script>RankList.init({type: 'hot2', descMap: {}});</script>")
        page1 = response(payload={"code": 100, "html": card(1, 1) + card(2, 2), "count": 2, "nextpage": 1})
        page2 = response(payload={"code": 100, "html": card(2, 2) + card(3, 3), "count": 2, "nextpage": 0})
        with patch.object(self.scraper, "_get", side_effect=[page, page1, page2]) as get:
            items = self.scraper.fetch("active")
        self.assertEqual([i.rank for i in items], [1, 2, 3])
        self.assertEqual(get.call_args_list[1].kwargs["params"]["type"], "hot2")
        self.assertEqual(get.call_args_list[2].kwargs["params"]["offset"], 2)
        self.assertEqual(get.call_args_list[2].kwargs["params"]["page"], 2)

    def test_invalid_api_payloads_are_not_saved_as_rankings(self):
        for payload in ({"code": 0}, {"code": 100, "html": "<li>热门榜</li>"},
                        {"code": 100, "html": None}, []):
            with self.subTest(payload=payload):
                page = response("<script>RankList.init({type: 'expect'});</script>")
                with patch.object(self.scraper, "_get", side_effect=[page, response(payload=payload)]):
                    self.assertEqual(self.scraper.fetch("reservation"), [])

    def test_failed_later_page_discards_incomplete_snapshot(self):
        self.scraper.TOP_N = 3
        page = response("<script>RankList.init({type: 'expect'});</script>")
        page1 = response(payload={"code": 100, "html": card(1, 1), "count": 1, "nextpage": 1})
        with patch.object(self.scraper, "_get", side_effect=[page, page1, RuntimeError("network failed")]):
            self.assertEqual(self.scraper.fetch("reservation"), [])

    def test_unknown_rank_type_does_not_fall_back_to_hot(self):
        with patch.object(self.scraper, "_get") as get:
            self.assertEqual(self.scraper.fetch("revenue"), [])
            get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
