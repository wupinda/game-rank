"""
竞品动态监控 — 深度信息抓取 + AI 分析

当检测到排名异动后，针对发生异动的平台抓取评分/更新日志/近期评论，
然后调用 Claude Haiku 分析异动原因。

平台分档：
  A 档（全量）：appstore*, taptap, steam*
  B 档（评分）：googleplay*
  C 档（跳过）：其余
"""
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/124.0.0.0 Safari/537.36")


class CompetitorMonitor:
    def __init__(self, proxies: dict = None, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": _UA})
        if proxies:
            self.session.proxies.update(proxies)

    def _get(self, url, **kwargs):
        return self.session.get(url, timeout=self.timeout, **kwargs)

    # ── A 档: App Store ────────────────────────────────────────────────────────

    def fetch_appstore(self, app_id: str, country: str = "cn") -> dict:
        result: dict = {}
        try:
            r = self._get(
                f"https://itunes.apple.com/lookup",
                params={"id": app_id, "country": country},
            )
            r.raise_for_status()
            data = r.json()
            if data.get("resultCount", 0) > 0:
                app = data["results"][0]
                result["rating"]   = round(float(app.get("averageUserRating") or 0), 1)
                result["version"]  = app.get("version", "")
                result["whatsnew"] = (app.get("releaseNotes") or "")[:500]
        except Exception as e:
            logger.warning(f"AppStore lookup [{country}/{app_id}] 失败: {e}")

        try:
            rr = self._get(
                f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
            )
            rr.raise_for_status()
            feed = rr.json().get("feed", {})
            entries = feed.get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]
            reviews = []
            for entry in entries[:10]:
                title   = (entry.get("title", {}).get("label") or "").strip()
                content = (entry.get("content", {}).get("label") or "").strip()
                if content:
                    reviews.append(f"{title}：{content}" if title else content)
            result["reviews"] = reviews
        except Exception as e:
            logger.warning(f"AppStore reviews [{country}/{app_id}] 失败: {e}")
            result.setdefault("reviews", [])

        return result

    # ── A 档: TapTap ──────────────────────────────────────────────────────────

    def fetch_taptap(self, app_id: str) -> dict:
        result: dict = {}
        headers = {
            "User-Agent": _UA,
            "X-UA": "V=1&PN=TapTap&VN_CODE=2010600&LOC=CN&LANG=zh_CN&CH=default",
        }
        try:
            r = self._get(
                "https://www.taptap.cn/webapiv2/app/v3/detail",
                params={"app_id": app_id},
                headers=headers,
            )
            r.raise_for_status()
            data = r.json().get("data", {})
            app  = data.get("app", {})
            result["rating"] = round(float((app.get("stat") or {}).get("rating") or 0), 1)
        except Exception as e:
            logger.warning(f"TapTap detail [{app_id}] 失败: {e}")

        try:
            r2 = self._get(
                "https://www.taptap.cn/webapiv2/app/v2/update-logs",
                params={"app_id": app_id, "limit": 3},
                headers=headers,
            )
            r2.raise_for_status()
            logs = r2.json().get("data", {}).get("list", [])
            if logs:
                result["whatsnew"] = (logs[0].get("content") or "")[:500]
        except Exception as e:
            logger.warning(f"TapTap update-logs [{app_id}] 失败: {e}")

        try:
            r3 = self._get(
                "https://www.taptap.cn/webapiv2/review/v3/app-comments",
                params={"app_id": app_id, "order": "new", "limit": 15},
                headers=headers,
            )
            r3.raise_for_status()
            comments = r3.json().get("data", {}).get("list", [])
            reviews = []
            for c in comments:
                body = (c.get("moment") or {}).get("review") or {}
                text = (body.get("contents") or [{}])[0].get("text", "")
                if text:
                    reviews.append(text[:200])
            result["reviews"] = reviews
        except Exception as e:
            logger.warning(f"TapTap reviews [{app_id}] 失败: {e}")
            result.setdefault("reviews", [])

        return result

    # ── A 档: Steam ───────────────────────────────────────────────────────────

    def fetch_steam(self, app_id: str) -> dict:
        result: dict = {}
        try:
            r = self._get(
                f"https://store.steampowered.com/appreviews/{app_id}",
                params={"json": "1", "language": "schinese", "num_per_page": "20",
                        "review_type": "all", "purchase_type": "all"},
            )
            r.raise_for_status()
            data = r.json()
            reviews = [
                rev.get("review", "")[:200]
                for rev in data.get("reviews", [])
                if rev.get("review", "").strip()
            ][:15]
            result["reviews"] = reviews
            summary = data.get("query_summary", {})
            total = summary.get("total_reviews", 0)
            pos   = summary.get("total_positive", 0)
            if total:
                result["rating"] = round(pos / total * 10, 1)
        except Exception as e:
            logger.warning(f"Steam reviews [{app_id}] 失败: {e}")
            result.setdefault("reviews", [])

        try:
            rn = self._get(
                "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/",
                params={"appid": app_id, "count": "3", "maxlength": "500"},
            )
            rn.raise_for_status()
            items = rn.json().get("appnews", {}).get("newsitems", [])
            if items:
                result["whatsnew"] = items[0].get("contents", "")[:500]
        except Exception as e:
            logger.warning(f"Steam news [{app_id}] 失败: {e}")

        return result

    # ── B 档: Google Play ─────────────────────────────────────────────────────

    def fetch_googleplay(self, package_id: str, country: str = "cn") -> dict:
        result: dict = {}
        try:
            gl = country if country != "cn" else "CN"
            r = self._get(
                "https://play.google.com/store/apps/details",
                params={"id": package_id, "hl": "zh", "gl": gl.upper()},
            )
            r.raise_for_status()
            import re
            m = re.search(r'"starRating":\s*"?([\d.]+)"?', r.text)
            if m:
                result["rating"] = round(float(m.group(1)), 1)
            wn = re.search(r'"recentChangesHtml":\s*"([^"]{10,500})"', r.text)
            if wn:
                result["whatsnew"] = wn.group(1).replace("\\n", "\n")[:500]
        except Exception as e:
            logger.warning(f"Google Play [{country}/{package_id}] 失败: {e}")
        result.setdefault("reviews", [])
        return result

    # ── 统一入口 ──────────────────────────────────────────────────────────────

    def fetch_platform_detail(self, platform: str, app_id: str) -> dict:
        if not app_id:
            return {}
        try:
            if platform.startswith("appstore"):
                country = platform.split("_")[1] if "_" in platform else "cn"
                return self.fetch_appstore(app_id, country)
            elif platform == "taptap":
                return self.fetch_taptap(app_id)
            elif platform.startswith("steam"):
                return self.fetch_steam(app_id)
            elif platform.startswith("googleplay"):
                country = platform.split("_")[1] if "_" in platform else "cn"
                return self.fetch_googleplay(app_id, country)
            else:
                return {}  # C 档：跳过
        except Exception as e:
            logger.warning(f"fetch_platform_detail [{platform}/{app_id}] 失败: {e}")
            return {}

    # ── Claude Haiku AI 分析 ──────────────────────────────────────────────────

    def analyze_with_ai(
        self,
        game_name: str,
        rank_changes: dict,
        platform_details: dict,
        reviews_sample: str = "",
    ) -> str:
        api_key  = os.environ.get("LLM_PROXY_API_KEY", "")
        base_url = os.environ.get("LLM_PROXY_BASE_URL", "https://llm-proxy.lilithgames.com/v1")
        model    = os.environ.get("LLM_PROXY_MODEL", "claude-haiku-4-5-20251001")
        if not api_key:
            return "(未配置 LLM_PROXY_API_KEY，跳过 AI 分析)"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            return "(openai 未安装，跳过 AI 分析)"

        change_lines = []
        for plt, chg in rank_changes.items():
            t, y = chg.get("today"), chg.get("yesterday")
            if t is None:
                change_lines.append(f"  {plt}: 跌出榜（前日 #{y}）")
            elif y is None:
                change_lines.append(f"  {plt}: 新进榜 #{t}")
            else:
                direction = "上升" if y > t else "下降"
                change_lines.append(f"  {plt}: #{y} → #{t}（{direction} {abs(y - t)} 名）")

        detail_lines = []
        for plt, d in platform_details.items():
            parts = []
            if d.get("rating"):
                parts.append(f"评分 {d['rating']}")
            if d.get("version"):
                parts.append(f"版本 {d['version']}")
            if d.get("whatsnew"):
                parts.append(f"更新内容：{d['whatsnew'][:200]}")
            if parts:
                detail_lines.append(f"  {plt}: " + "，".join(parts))

        prompt = (
            f"以下是手游《{game_name}》的排名异动数据，请用中文分析可能的原因（200字以内）。\n\n"
            f"排名变化：\n" + "\n".join(change_lines) + "\n\n"
            + (f"各平台详情：\n" + "\n".join(detail_lines) + "\n\n" if detail_lines else "")
            + (f"近期评论摘样：\n{reviews_sample[:1000]}\n\n" if reviews_sample else "")
            + "请直接输出分析结论，不需要标题或序号。"
        )

        try:
            resp = client.chat.completions.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM Proxy 分析失败: {e}")
            return f"(AI 分析失败: {e})"
