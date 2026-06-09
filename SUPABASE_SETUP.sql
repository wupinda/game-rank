-- ============================================================
-- 在 Supabase SQL Editor 中运行本文件（一次性）
-- ============================================================

-- 1. 排行榜数据表
CREATE TABLE IF NOT EXISTS rankings (
    id         BIGSERIAL PRIMARY KEY,
    platform   TEXT    NOT NULL,
    rank_type  TEXT    NOT NULL,
    rank_pos   INTEGER NOT NULL,
    game_name  TEXT    NOT NULL,
    game_id    TEXT    DEFAULT '',
    developer  TEXT    DEFAULT '',
    icon_url   TEXT    DEFAULT '',
    rating     REAL    DEFAULT 0,
    fetch_date TEXT    NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rankings_main ON rankings(platform, rank_type, fetch_date);

-- 2. 开测表数据表
CREATE TABLE IF NOT EXISTS launches (
    id          BIGSERIAL PRIMARY KEY,
    platform    TEXT NOT NULL,
    game_name   TEXT NOT NULL,
    launch_time TEXT NOT NULL,
    launch_type TEXT DEFAULT '',
    developer   TEXT DEFAULT '',
    game_id     TEXT DEFAULT '',
    icon_url    TEXT DEFAULT '',
    fetch_date  TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_launches_main ON launches(platform, fetch_date);

-- 3. 辅助函数（用于高效获取不重复日期/平台列表）
CREATE OR REPLACE FUNCTION get_rank_dates()
RETURNS TABLE (fetch_date TEXT) LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT DISTINCT fetch_date FROM rankings ORDER BY fetch_date DESC;
$$;

CREATE OR REPLACE FUNCTION get_launch_dates()
RETURNS TABLE (fetch_date TEXT) LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT DISTINCT fetch_date FROM launches ORDER BY fetch_date DESC;
$$;

CREATE OR REPLACE FUNCTION get_rank_platforms()
RETURNS TABLE (platform TEXT) LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT DISTINCT platform FROM rankings ORDER BY platform;
$$;

-- 4. 开放 anon 角色的读写权限（内部工具，无需行级限制）
ALTER TABLE rankings ENABLE ROW LEVEL SECURITY;
ALTER TABLE launches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_rankings" ON rankings FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_launches" ON launches FOR ALL TO anon USING (true) WITH CHECK (true);
