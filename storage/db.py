import os
from typing import List, Optional

from supabase import create_client, Client
from scrapers.base import RankItem, LaunchItem


class Database:
    def __init__(self, url: str = None, key: str = None):
        url = url or os.environ.get("SUPABASE_URL", "")
        key = key or os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError(
                "Supabase 凭据缺失，请在 config.yaml 的 supabase 节或环境变量 "
                "SUPABASE_URL / SUPABASE_KEY 中填写。"
            )
        self._client: Client = create_client(url, key)

    # ── write ──────────────────────────────────────────────────────────────────

    def save(self, items: List[RankItem]):
        if not items:
            return
        rows = [
            {
                "platform":   it.platform,
                "rank_type":  it.rank_type,
                "rank_pos":   it.rank,
                "game_name":  it.name,
                "game_id":    it.game_id or "",
                "developer":  it.developer or "",
                "icon_url":   it.icon_url or "",
                "rating":     it.rating or 0.0,
                "fetch_date": it.fetch_date,
            }
            for it in items
        ]
        for i in range(0, len(rows), 500):
            self._client.table("rankings").insert(rows[i : i + 500]).execute()

    def delete_by_date(self, fetch_date: str, platform: str = None):
        q = self._client.table("rankings").delete().eq("fetch_date", fetch_date)
        if platform:
            q = q.eq("platform", platform)
        q.execute()

    def save_launches(self, items: List[LaunchItem]):
        if not items:
            return
        rows = [
            {
                "platform":    it.platform,
                "game_name":   it.game_name,
                "launch_time": it.launch_time,
                "launch_type": it.launch_type or "",
                "developer":   it.developer or "",
                "game_id":     it.game_id or "",
                "icon_url":    it.icon_url or "",
                "fetch_date":  it.fetch_date,
            }
            for it in items
        ]
        self._client.table("launches").insert(rows).execute()

    def delete_launches_by_date(self, fetch_date: str, platform: str = None):
        q = self._client.table("launches").delete().eq("fetch_date", fetch_date)
        if platform:
            q = q.eq("platform", platform)
        q.execute()

    # ── read ───────────────────────────────────────────────────────────────────

    def query(
        self,
        platform: Optional[str] = None,
        rank_type: Optional[str] = None,
        fetch_date: Optional[str] = None,
    ) -> List[dict]:
        q = (
            self._client.table("rankings")
            .select("*")
            .order("platform")
            .order("rank_type")
            .order("rank_pos")
            .limit(5000)
        )
        if platform:
            q = q.eq("platform", platform)
        if rank_type:
            q = q.eq("rank_type", rank_type)
        if fetch_date:
            q = q.eq("fetch_date", fetch_date)
        return q.execute().data

    def query_launches(
        self,
        platform: Optional[str] = None,
        fetch_date: Optional[str] = None,
    ) -> List[dict]:
        q = (
            self._client.table("launches")
            .select("*")
            .order("launch_time")
            .order("platform")
            .limit(2000)
        )
        if platform:
            q = q.eq("platform", platform)
        if fetch_date:
            q = q.eq("fetch_date", fetch_date)
        return q.execute().data

    def available_dates(self) -> List[str]:
        return [r["fetch_date"] for r in self._client.rpc("get_rank_dates").execute().data]

    def available_launch_dates(self) -> List[str]:
        return [r["fetch_date"] for r in self._client.rpc("get_launch_dates").execute().data]

    def available_platforms(self) -> List[str]:
        return [r["platform"] for r in self._client.rpc("get_rank_platforms").execute().data]

    def get_platforms_for_game(self, game_name: str) -> List[str]:
        rows = (
            self._client.table("rankings")
            .select("platform")
            .eq("game_name", game_name)
            .execute()
            .data
        )
        return sorted({r["platform"] for r in rows})

    # ── competitors ────────────────────────────────────────────────────────────

    def get_competitors(self) -> List[dict]:
        return self._client.table("competitors").select("*").order("game_name").execute().data

    def add_competitor(self, game_name: str, notes: str = ""):
        self._client.table("competitors").upsert(
            {"game_name": game_name, "notes": notes},
            on_conflict="game_name",
        ).execute()

    def remove_competitor(self, game_name: str):
        self._client.table("competitors").delete().eq("game_name", game_name).execute()

    def save_anomaly(self, record: dict):
        self._client.table("competitor_anomalies").upsert(
            record, on_conflict="game_name,fetch_date"
        ).execute()

    def get_anomalies(self, days: int = 30) -> List[dict]:
        from datetime import date, timedelta
        since = (date.today() - timedelta(days=days)).isoformat()
        return (
            self._client.table("competitor_anomalies")
            .select("*")
            .gte("fetch_date", since)
            .order("fetch_date", desc=True)
            .order("game_name")
            .execute()
            .data
        )

    def trend(self, game_name: str, platform: str, rank_type: str) -> List[dict]:
        return (
            self._client.table("rankings")
            .select("fetch_date,rank_pos")
            .eq("game_name", game_name)
            .eq("platform", platform)
            .eq("rank_type", rank_type)
            .order("fetch_date")
            .execute()
            .data
        )
