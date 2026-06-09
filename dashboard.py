"""
游戏排行榜 - Streamlit 可视化面板
启动方式：streamlit run dashboard.py
或通过：python main.py dashboard
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st
import plotly.express as px

from storage import Database
from scrapers.base import PLATFORMS, RANK_TYPES
from utils import Exporter

st.set_page_config(
    page_title="游戏渠道排行榜",
    page_icon="🎮",
    layout="wide",
)

OUTPUT_DIR = "./data"

_OVERSEAS_PLATFORMS = {
    "rustore",
    "appstore_us", "appstore_jp", "appstore_kr", "appstore_gb",
    "googleplay", "googleplay_us", "googleplay_jp", "googleplay_kr", "googleplay_gb",
    "steam", "steam_us", "steam_jp", "steam_kr", "steam_gb",
    "epicgames",
    "msstore", "msstore_us", "msstore_jp", "msstore_kr", "msstore_gb",
}


@st.cache_resource
def get_db():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    return Database(url=url, key=key)


def load_data(db: Database, platform=None, rank_type=None, fetch_date=None) -> pd.DataFrame:
    rows = db.query(platform=platform, rank_type=rank_type, fetch_date=fetch_date)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["平台"]   = df["platform"].map(lambda x: PLATFORMS.get(x, x))
    df["榜单"]   = df["rank_type"].map(lambda x: RANK_TYPES.get(x, x))
    df["排名"]   = df["rank_pos"]
    df["游戏名"] = df["game_name"]
    df["开发商"] = df["developer"]
    df["评分"]   = df["rating"].apply(lambda x: round(x, 1) if x else "")
    return df


def build_rank_change_map(db: Database, sel_date: str, rank_type: str) -> dict:
    """返回 {(platform, game_name): change_str}，无前日数据时返回空 dict。"""
    dates = db.available_dates()
    if sel_date not in dates:
        return {}
    idx = dates.index(sel_date)
    if idx + 1 >= len(dates):
        return {}
    prev_date = dates[idx + 1]
    prev_rows = db.query(rank_type=rank_type, fetch_date=prev_date)
    prev_lookup = {(r["platform"], r["game_name"]): r["rank_pos"] for r in prev_rows}
    curr_rows = db.query(rank_type=rank_type, fetch_date=sel_date)
    change_map = {}
    for r in curr_rows:
        key = (r["platform"], r["game_name"])
        prev_rank = prev_lookup.get(key)
        curr_rank = r["rank_pos"]
        if prev_rank is None:
            change_map[key] = "NEW"
        else:
            diff = prev_rank - curr_rank  # 正数 = 名次上升
            if diff > 0:
                change_map[key] = f"↑{diff}"
            elif diff < 0:
                change_map[key] = f"↓{abs(diff)}"
            else:
                change_map[key] = ""
    return change_map


def _analyze_movement(db, game: str, plt_key: str, rank_type: str,
                      sel_date: str, change_map: dict) -> str:
    """返回游戏排名变化的简短分析（连续趋势 + 多平台同步），无信号时返回空串。"""
    dates = db.available_dates()
    if sel_date not in dates:
        return ""
    idx = dates.index(sel_date)

    history = []
    for i in range(min(5, idx + 1)):
        rows = db.query(platform=plt_key, rank_type=rank_type, fetch_date=dates[idx + i])
        rank_map = {r["game_name"]: r["rank_pos"] for r in rows}
        history.append(rank_map.get(game))

    clues = []

    consecutive, direction = 0, None
    for i in range(len(history) - 1):
        curr, prev = history[i], history[i + 1]
        if curr is None or prev is None:
            break
        d = "up" if curr < prev else ("down" if curr > prev else None)
        if d is None:
            break
        if direction is None:
            direction, consecutive = d, 1
        elif d == direction:
            consecutive += 1
        else:
            break
    if consecutive >= 2:
        clues.append(f"连续{consecutive}日{'上涨' if direction == 'up' else '下滑'}")

    curr_chg = change_map.get((plt_key, game), "")
    sync = sum(
        1 for (pk, gm), chg in change_map.items()
        if gm == game and pk != plt_key
        and (("↑" in curr_chg and "↑" in chg) or ("↓" in curr_chg and "↓" in chg))
    )
    if sync >= 2:
        clues.append(f"{sync + 1}平台同步")
    elif sync == 1:
        clues.append("双平台同步")

    return "，".join(clues)


# ── 侧边栏 ─────────────────────────────────────────────────────────────────
st.sidebar.title("🎮 游戏排行榜")
st.sidebar.divider()

db = get_db()

dates = db.available_dates()
if not dates:
    st.warning("数据库暂无数据，请先运行 `python main.py fetch` 抓取数据。")
    st.code("python main.py fetch", language="bash")
    st.stop()

# 页签导航（放最前，后续选项依赖它）
_PAGES = ["国内排行榜", "国内开测表", "海外排行榜"]
sel_page = st.sidebar.radio("📑 页签", _PAGES, key="sel_page", label_visibility="collapsed")
st.sidebar.divider()

sel_date = st.sidebar.selectbox("📅 日期", dates, index=0)

sel_platform = None

# 榜单类型——海外只显示下载榜/畅销榜/活跃榜（活跃榜仅 Steam 有）
if sel_page == "国内开测表":
    sel_rank_type = None
elif sel_page == "海外排行榜":
    _overseas_rank_opts = {"下载榜": "download", "畅销榜": "revenue", "活跃榜": "active"}
    sel_rank_label = st.sidebar.selectbox("📊 榜单类型", list(_overseas_rank_opts.keys()))
    sel_rank_type = _overseas_rank_opts[sel_rank_label]
else:
    rank_type_labels = {"全部": None, **{v: k for k, v in RANK_TYPES.items()}}
    _rank_options = list(rank_type_labels.keys())
    _default_rank_idx = _rank_options.index("预约榜") if "预约榜" in _rank_options else 0
    sel_rank_label = st.sidebar.selectbox(
        "📊 榜单类型",
        options=_rank_options,
        index=_default_rank_idx,
    )
    sel_rank_type = rank_type_labels[sel_rank_label]

st.sidebar.divider()

# 自动刷新控制
auto_refresh = st.sidebar.toggle("⏱ 自动刷新", value=False)
if auto_refresh:
    refresh_mins = st.sidebar.selectbox(
        "刷新间隔",
        options=[1, 5, 10, 30],
        index=1,
        format_func=lambda x: f"{x} 分钟",
    )
else:
    refresh_mins = 5

st.sidebar.divider()
if st.sidebar.button("🔄 立即抓取数据"):
    with st.spinner("正在抓取，请稍候…"):
        import subprocess
        result = subprocess.run(
            [sys.executable, "main.py", "fetch"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    if result.returncode == 0:
        st.sidebar.success("抓取完成！")
        st.rerun()
    else:
        st.sidebar.error(f"抓取失败：{result.stderr[:200]}")


# ── 数据展示（支持自动刷新）─────────────────────────────────────────────────
def render_data(sel_date, sel_platform, sel_rank_type):
    df = load_data(db, platform=sel_platform, rank_type=sel_rank_type, fetch_date=sel_date)
    if not df.empty:
        df = df[~df["platform"].isin(_OVERSEAS_PLATFORMS)]

    st.title(f"游戏渠道排行榜 — {sel_date}")

    # 平台显示名 -> platform key 的映射（全量，供表格与趋势图共用）
    plt_label_to_key = {}
    if not df.empty:
        plt_label_to_key = (
            df[["platform", "平台"]].drop_duplicates()
            .set_index("平台")["platform"].to_dict()
        )

    # 多平台对比视图
    if not df.empty and sel_rank_type:
        st.subheader(f"📋 {RANK_TYPES.get(sel_rank_type, sel_rank_type)} — Top 20 对比")

        change_map = build_rank_change_map(db, sel_date, sel_rank_type)

        _all_plt_labels = sorted(plt_label_to_key.keys())
        _sel_plt_labels = st.multiselect(
            "展示渠道",
            options=_all_plt_labels,
            default=_all_plt_labels,
            key=f"plt_sort_{sel_date}_{sel_rank_type}",
            label_visibility="collapsed",
        )
        df_view = df[df["平台"].isin(_sel_plt_labels)] if _sel_plt_labels else df

        # pivot 使用原始游戏名（不混入变化标记）
        pivot = df_view.pivot_table(
            index="排名", columns="平台", values="游戏名", aggfunc="first"
        ).reset_index()

        # 按拖拽顺序排列列（而非 pandas 默认的字母序）
        game_cols = [c for c in _sel_plt_labels if c in pivot.columns]

        # ── 今日动态概述 ──────────────────────────────────────────────────────
        if change_map:
            # 1. 各平台涨幅最大 / 跌幅最大
            risers, fallers = [], []
            for (plt_key, game), chg in change_map.items():
                if plt_key not in {plt_label_to_key.get(c) for c in game_cols}:
                    continue
                if "↑" in chg:
                    risers.append((int(chg.replace("↑", "")), game, plt_key))
                elif "↓" in chg:
                    fallers.append((int(chg.replace("↓", "")), game, plt_key))

            risers.sort(reverse=True)
            fallers.sort(reverse=True)

            # 2. 多平台同时上榜（≥3个平台）
            from collections import Counter
            game_plt_count = Counter()
            for (plt_key, game) in change_map.keys():
                if plt_key in {plt_label_to_key.get(c) for c in game_cols}:
                    game_plt_count[game] += 1
            cross_plts = [(cnt, g) for g, cnt in game_plt_count.items() if cnt >= 3]
            cross_plts.sort(reverse=True)

            # 3. 渲染概述卡片
            lines = []
            if risers:
                parts = []
                for n, g, pk in risers[:3]:
                    a = _analyze_movement(db, g, pk, sel_rank_type, sel_date, change_map)
                    suffix = f" *({a})*" if a else ""
                    parts.append(f"{PLATFORMS.get(pk, pk)}·**{g}** ↑{n}{suffix}")
                lines.append(("📈 最大涨幅", "  |  ".join(parts)))
            if fallers:
                parts = []
                for n, g, pk in fallers[:3]:
                    a = _analyze_movement(db, g, pk, sel_rank_type, sel_date, change_map)
                    suffix = f" *({a})*" if a else ""
                    parts.append(f"{PLATFORMS.get(pk, pk)}·**{g}** ↓{n}{suffix}")
                lines.append(("📉 最大跌幅", "  |  ".join(parts)))
            if cross_plts:
                parts = [f"**{g}**（{cnt}个平台）" for cnt, g in cross_plts[:4]]
                lines.append(("🔥 多平台上榜", "  |  ".join(parts)))

            if lines:
                with st.container(border=True):
                    st.caption(f"📊 今日动态 — {sel_date}")
                    for icon_label, content in lines:
                        st.markdown(f"**{icon_label}**：{content}")

        # 构建 HTML 表格（斑马纹）
        DIVIDER  = "border-right:2px solid #d1d5db"
        COL_W    = "width:220px;min-width:220px;max-width:220px"
        th_rank  = f"padding:8px 10px;border-bottom:2px solid #d1d5db;text-align:center;font-weight:600;width:52px;min-width:52px;{DIVIDER}"
        th_game  = f"padding:8px 14px;border-bottom:2px solid #d1d5db;font-weight:600;{COL_W};{DIVIDER}"

        header = f'<th style="{th_rank}">排名</th>' + "".join(
            f'<th style="{th_game}">{col}</th>' for col in game_cols
        )

        rows_html = ""
        for idx, (_, row) in enumerate(pivot.iterrows()):
            rank_val = int(row["排名"])
            row_bg   = "background:#f8fafc" if idx % 2 == 1 else "background:#ffffff"
            td_rank  = f"padding:6px 10px;text-align:center;color:#6b7280;width:52px;{DIVIDER};{row_bg}"
            td_game  = f"padding:6px 12px;{COL_W};{DIVIDER};{row_bg}"
            cells = f'<td style="{td_rank}">{rank_val}</td>'
            for col in game_cols:
                game = row.get(col)
                if game is None or (isinstance(game, float) and pd.isna(game)):
                    cells += f'<td style="{td_game}"></td>'
                    continue
                plt_key = plt_label_to_key.get(col, "")
                chg = change_map.get((plt_key, game), None) if change_map else None
                if chg is None:
                    badge = ""
                elif "↑" in chg:
                    num = chg.replace("↑", "")
                    badge = f'<span style="color:#16a34a;font-weight:700;flex-shrink:0">▲{num}</span>'
                elif "↓" in chg:
                    num = chg.replace("↓", "")
                    badge = f'<span style="color:#dc2626;font-weight:700;flex-shrink:0">▼{num}</span>'
                elif chg == "NEW":
                    badge = '<span style="color:#2563eb;font-weight:700;flex-shrink:0">NEW</span>'
                else:
                    badge = '<span style="color:#9ca3af;flex-shrink:0">-</span>'
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="overflow:hidden;text-overflow:ellipsis">{game}</span>'
                    f'{badge}'
                    f'</div>'
                )
                cells += f'<td style="{td_game}">{cell_inner}</td>'
            rows_html += f"<tr>{cells}</tr>"

        table_html = f"""
        <div style="overflow:auto;max-height:620px;border:1px solid #d1d5db;border-radius:8px">
          <table style="border-collapse:collapse;font-size:14px;table-layout:fixed">
            <thead style="position:sticky;top:0;background:#f1f5f9;z-index:1">
              <tr>{header}</tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """
        st.html(table_html)
        if change_map:
            st.caption("▲▼ 数字表示与前一日相比的排名变化，NEW 表示新上榜，- 表示未变化")

    # 导出
    if not df.empty:
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            if st.button("📥 导出 Excel"):
                from scrapers.base import RankItem
                items = [
                    RankItem(
                        rank=int(r["rank_pos"]),
                        name=r["game_name"],
                        platform=r["platform"],
                        rank_type=r["rank_type"],
                        game_id=r.get("game_id", ""),
                        developer=r.get("developer", ""),
                        icon_url=r.get("icon_url", ""),
                        rating=float(r.get("rating") or 0),
                        fetch_date=r["fetch_date"],
                    )
                    for r in db.query(
                        platform=sel_platform,
                        rank_type=sel_rank_type,
                        fetch_date=sel_date,
                    )
                    if r["platform"] not in _OVERSEAS_PLATFORMS
                ]
                exp  = Exporter(OUTPUT_DIR)
                path = exp.to_excel(items, sel_date)
                with open(path, "rb") as f:
                    st.download_button(
                        label="⬇ 下载 Excel 文件",
                        data=f,
                        file_name=os.path.basename(path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

    # 趋势图
    st.divider()
    st.subheader("📈 排名趋势（选择游戏查看历史变化）")
    game_options = sorted(df["游戏名"].unique().tolist()) if not df.empty else []
    if game_options:
        tr_col1, tr_col2 = st.columns([3, 1])
        with tr_col1:
            sel_game = st.selectbox("选择游戏", game_options)
        with tr_col2:
            _game_plt_labels = (
                sorted(df[df["游戏名"] == sel_game]["平台"].unique().tolist())
                if sel_game else []
            )
            sel_trend_plt_label = (
                st.selectbox("选择平台", _game_plt_labels)
                if _game_plt_labels else None
            )
        _trend_plt_key = plt_label_to_key.get(sel_trend_plt_label, "") if sel_trend_plt_label else ""
        if sel_game and _trend_plt_key and sel_rank_type:
            trend_rows = db.trend(sel_game, _trend_plt_key, sel_rank_type)
            if len(trend_rows) > 1:
                tdf = pd.DataFrame(trend_rows)
                tdf.columns = ["日期", "排名"]
                fig = px.line(
                    tdf, x="日期", y="排名", markers=True,
                    title=f"{sel_game} 排名趋势（{sel_trend_plt_label} · {RANK_TYPES.get(sel_rank_type, sel_rank_type)}）",
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("需要多天数据才能显示趋势图，请继续每日抓取。")
        else:
            st.info("请选择游戏和平台后查看趋势。")


_OVERSEAS_PLT_ORDER = [
    "rustore",
    "appstore_us", "appstore_jp", "appstore_kr", "appstore_gb",
    "googleplay_us", "googleplay_jp", "googleplay_kr", "googleplay_gb",
]
_PC_PLT_ORDER = [
    "steam_us", "steam_jp", "steam_kr", "steam_gb",
    "epicgames",
    "msstore_us", "msstore_jp", "msstore_kr", "msstore_gb",
]
_OVERSEAS_RANK_TYPES = {"download", "revenue", "active"}

def render_overseas(db: Database, sel_date: str, sel_rank_type: str):
    st.title(f"海外排行榜 — {sel_date}")

    overseas_dates = db.available_dates()
    if not overseas_dates:
        st.info("暂无海外数据，请先运行 `python main.py fetch` 抓取数据。")
        st.code("python main.py fetch", language="bash")
        return

    active_date = sel_date if sel_date in overseas_dates else overseas_dates[0]

    # 海外只有下载榜/畅销榜，若侧边栏选了不支持的类型则回落到下载榜
    rank_type_ov = sel_rank_type if sel_rank_type in _OVERSEAS_RANK_TYPES else "download"

    # Load data for each overseas platform
    present_plts = []
    plt_data: dict[str, list] = {}
    for plt_key in _OVERSEAS_PLT_ORDER:
        rows = db.query(platform=plt_key, rank_type=rank_type_ov, fetch_date=active_date)
        if rows:
            present_plts.append(plt_key)
            plt_data[plt_key] = rows

    # Pre-load PC data too, so we can check if any data exists at all
    pc_plts_pre = []
    pc_data_pre: dict[str, list] = {}
    for plt_key in _PC_PLT_ORDER:
        rows = db.query(platform=plt_key, rank_type=rank_type_ov, fetch_date=active_date)
        if rows:
            pc_plts_pre.append(plt_key)
            pc_data_pre[plt_key] = rows

    if not present_plts and not pc_plts_pre:
        st.info(f"当前日期 {active_date} 暂无海外数据，请先抓取。")
        return

    # Build change map (compared to previous day) — reuse existing util
    change_map = build_rank_change_map(db, active_date, rank_type_ov)

    st.subheader("📱 移动平台排行榜")

    # HTML table（斑马纹，与国内榜一致）
    DIVIDER = "border-right:2px solid #d1d5db"
    COL_W   = "width:220px;min-width:220px;max-width:220px"
    th_rank = f"padding:8px 10px;border-bottom:2px solid #d1d5db;text-align:center;font-weight:600;width:52px;min-width:52px;{DIVIDER}"
    th_game = f"padding:8px 14px;border-bottom:2px solid #d1d5db;font-weight:600;{COL_W};{DIVIDER}"

    def _make_badge(chg):
        if chg is None:
            return ""
        if "↑" in chg:
            return f'<span style="color:#16a34a;font-weight:700;flex-shrink:0">▲{chg.replace("↑","")}</span>'
        if "↓" in chg:
            return f'<span style="color:#dc2626;font-weight:700;flex-shrink:0">▼{chg.replace("↓","")}</span>'
        if chg == "NEW":
            return '<span style="color:#2563eb;font-weight:700;flex-shrink:0">NEW</span>'
        return '<span style="color:#9ca3af;flex-shrink:0">-</span>'

    def _render_table(rank_maps, plt_keys, plt_lbls, max_rank):
        header = f'<th style="{th_rank}">排名</th>' + "".join(
            f'<th style="{th_game}">{lbl}</th>' for lbl in plt_lbls
        )
        rows_html = ""
        for idx, rank_val in enumerate(range(1, min(max_rank, 30) + 1)):
            row_bg  = "background:#f8fafc" if idx % 2 == 1 else "background:#ffffff"
            td_rank = f"padding:6px 10px;text-align:center;color:#6b7280;width:52px;{DIVIDER};{row_bg}"
            td_game = f"padding:6px 12px;{COL_W};{DIVIDER};{row_bg}"
            cells   = f'<td style="{td_rank}">{rank_val}</td>'
            for plt_key in plt_keys:
                game = rank_maps[plt_key].get(rank_val)
                if not game:
                    cells += f'<td style="{td_game}"></td>'
                    continue
                chg = change_map.get((plt_key, game), None) if change_map else None
                badge = _make_badge(chg)
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="overflow:hidden;text-overflow:ellipsis">{game}</span>'
                    f'{badge}</div>'
                )
                cells += f'<td style="{td_game}">{cell_inner}</td>'
            rows_html += f"<tr>{cells}</tr>"
        return f"""
        <div style="overflow:auto;max-height:620px;border:1px solid #d1d5db;border-radius:8px">
          <table style="border-collapse:collapse;font-size:14px;table-layout:fixed">
            <thead style="position:sticky;top:0;background:#f1f5f9;z-index:1">
              <tr>{header}</tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """

    def _render_summary(plt_keys, section_date):
        """在表格上方渲染今日动态概述（涨跌幅 / 新上榜 / 多平台）"""
        if not change_map:
            return
        from collections import Counter
        risers, fallers = [], []
        game_plt_count = Counter()
        for (pk, game), chg in change_map.items():
            if pk not in plt_keys:
                continue
            game_plt_count[game] += 1
            if "↑" in chg:
                risers.append((int(chg.replace("↑", "")), game, pk))
            elif "↓" in chg:
                fallers.append((int(chg.replace("↓", "")), game, pk))

        risers.sort(reverse=True)
        fallers.sort(reverse=True)
        cross_plts = sorted(
            [(cnt, g) for g, cnt in game_plt_count.items() if cnt >= 3],
            reverse=True,
        )
        lines = []
        if risers:
            parts = []
            for n, g, pk in risers[:3]:
                a = _analyze_movement(db, g, pk, rank_type_ov, active_date, change_map)
                suffix = f" *({a})*" if a else ""
                parts.append(f"{PLATFORMS.get(pk, pk)}·**{g}** ↑{n}{suffix}")
            lines.append(("📈 最大涨幅", "  |  ".join(parts)))
        if fallers:
            parts = []
            for n, g, pk in fallers[:3]:
                a = _analyze_movement(db, g, pk, rank_type_ov, active_date, change_map)
                suffix = f" *({a})*" if a else ""
                parts.append(f"{PLATFORMS.get(pk, pk)}·**{g}** ↓{n}{suffix}")
            lines.append(("📉 最大跌幅", "  |  ".join(parts)))
        if cross_plts:
            parts = [f"**{g}**（{cnt}个平台）" for cnt, g in cross_plts[:4]]
            lines.append(("🔥 多平台上榜", "  |  ".join(parts)))

        if lines:
            with st.container(border=True):
                st.caption(f"📊 今日动态 — {section_date}")
                for label, content in lines:
                    st.markdown(f"**{label}**：{content}")

    if present_plts:
        _mob_labels_all = [PLATFORMS.get(k, k) for k in present_plts]
        _mob_lbl_to_key = {PLATFORMS.get(k, k): k for k in present_plts}
        _sel_mob_labels = st.multiselect(
            "展示渠道",
            options=_mob_labels_all,
            default=_mob_labels_all,
            key=f"mob_plt_sort_{active_date}_{rank_type_ov}",
            label_visibility="collapsed",
        )
        present_plts = [_mob_lbl_to_key[l] for l in _sel_mob_labels if l in _mob_lbl_to_key]
        plt_labels = _sel_mob_labels

        rank_maps: dict[str, dict[int, str]] = {
            k: {r["rank_pos"]: r["game_name"] for r in plt_data[k]} for k in present_plts
        }
        max_rank = max((max(rm.keys()) for rm in rank_maps.values() if rm), default=20)
        _render_summary(set(present_plts), active_date)
        st.html(_render_table(rank_maps, present_plts, plt_labels, max_rank))
        if change_map:
            st.caption("▲▼ 数字表示与前一日相比的排名变化，NEW 表示新上榜，- 表示未变化")
    else:
        st.info("移动平台暂无该榜单数据。")

    # ── PC 平台排行榜 ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("💻 PC 平台排行榜")

    pc_plts = pc_plts_pre
    pc_data = pc_data_pre

    if not pc_plts:
        st.info(f"当前日期 {active_date} 暂无 PC 平台数据，请先抓取。")
        st.code("python main.py fetch --platform steam epicgames msstore", language="bash")
    else:
        _pc_labels_all = [PLATFORMS.get(k, k) for k in pc_plts]
        _pc_lbl_to_key = {PLATFORMS.get(k, k): k for k in pc_plts}
        _sel_pc_labels = st.multiselect(
            "展示渠道",
            options=_pc_labels_all,
            default=_pc_labels_all,
            key=f"pc_plt_sort_{active_date}_{rank_type_ov}",
            label_visibility="collapsed",
        )
        pc_plts = [_pc_lbl_to_key[l] for l in _sel_pc_labels if l in _pc_lbl_to_key]
        pc_labels = _sel_pc_labels

        pc_rank_maps: dict[str, dict[int, str]] = {
            k: {r["rank_pos"]: r["game_name"] for r in pc_data[k]} for k in pc_plts
        }
        pc_max_rank = max((max(rm.keys()) for rm in pc_rank_maps.values() if rm), default=20)
        _render_summary(set(pc_plts), active_date)
        st.html(_render_table(pc_rank_maps, pc_plts, pc_labels, pc_max_rank))


_LAUNCH_TYPE_STYLE = {
    "首发":   "color:#16a34a;font-weight:600",
    "公测":   "color:#16a34a;font-weight:600",
    "不删档": "color:#16a34a;font-weight:600",
    "预约":   "color:#2563eb",
    "删档":   "color:#d97706",
    "测试":   "color:#d97706",
}

def _launch_type_style(t: str) -> str:
    for k, v in _LAUNCH_TYPE_STYLE.items():
        if k in t:
            return v
    return "color:#6b7280"

_LAUNCH_PLT_ORDER = ["bilibili", "taptap", "kuaibao", "wegame"]

def render_launches(db: Database, sel_date: str, sel_platform=None):
    launch_dates = db.available_launch_dates()
    if not launch_dates:
        st.info("暂无开测数据，请先运行 `python main.py fetch` 抓取数据。")
        st.code("python main.py fetch", language="bash")
        return

    active_date = sel_date if sel_date in launch_dates else launch_dates[0]
    rows = db.query_launches(fetch_date=active_date)

    st.title(f"近期开测信息 — {active_date}")

    if not rows:
        st.info(f"当前日期 {active_date} 暂无开测数据。")
        return

    df = pd.DataFrame(rows)
    from datetime import date as _date_cls
    today_str = _date_cls.today().isoformat()

    df["_plt_label"] = df["platform"].map(lambda x: PLATFORMS.get(x, x))
    df["_date"]      = df["launch_time"].str[:10].apply(
        lambda x: x if (x and len(x) == 10) else "待定"
    )
    df["_time"]      = df["launch_time"].str[11:16]   # "HH:MM" or ""

    # ── 确定渠道列顺序 ──────────────────────────────────────────
    present_plts = set(df["platform"].unique())
    plt_keys  = [k for k in _LAUNCH_PLT_ORDER if k in present_plts]
    plt_keys += [k for k in present_plts if k not in _LAUNCH_PLT_ORDER]
    plt_labels = [PLATFORMS.get(k, k) for k in plt_keys]

    _all_launch_labels = plt_labels
    _lbl_to_key = {PLATFORMS.get(k, k): k for k in plt_keys}
    plt_labels = st.multiselect(
        "展示渠道",
        options=_all_launch_labels,
        default=_all_launch_labels,
        key=f"launch_plt_sort_{active_date}",
        label_visibility="collapsed",
    )
    plt_keys = [_lbl_to_key[l] for l in plt_labels if l in _lbl_to_key]

    # ── 按 (日期, 渠道) 聚合游戏列表 ─────────────────────────────
    from collections import defaultdict
    cell_map  = defaultdict(lambda: defaultdict(list))
    dates_set = set()
    for _, r in df.iterrows():
        dates_set.add(r["_date"])
        cell_map[r["_date"]][r["_plt_label"]].append({
            "name": r["game_name"],
            "type": r["launch_type"],
            "time": r["_time"],
        })

    # 只保留今天及之后的日期，待定放末尾
    sorted_dates = (
        sorted(d for d in dates_set if d != "待定" and d >= today_str)
        + (["待定"] if "待定" in dates_set else [])
    )

    # ── HTML 表格 ─────────────────────────────────────────────
    DIVIDER = "border-right:2px solid #d1d5db"
    TIME_W  = "width:96px;min-width:96px"
    COL_W   = "width:220px;min-width:220px;max-width:220px"
    th_time = f"padding:6px 10px;border-bottom:2px solid #e5e7eb;font-weight:600;{TIME_W};{DIVIDER}"
    th_plt  = f"padding:6px 14px;border-bottom:2px solid #e5e7eb;font-weight:600;{COL_W};{DIVIDER}"
    td_time = f"padding:5px 10px;border-bottom:1px solid #f3f4f6;vertical-align:top;color:#6b7280;{TIME_W};{DIVIDER}"
    td_cell = f"padding:5px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;{COL_W};{DIVIDER}"

    header = f'<th style="{th_time}">开测时间</th>' + "".join(
        f'<th style="{th_plt}">{p}</th>' for p in plt_labels
    )

    MAX_PER_CELL = 12
    rows_html = ""
    for date_key in sorted_dates:
        cells = f'<td style="{td_time}">{date_key}</td>'
        for plt_label in plt_labels:
            games = cell_map[date_key].get(plt_label, [])
            if not games:
                cells += f'<td style="{td_cell}"></td>'
                continue
            items_html = ""
            shown = games[:MAX_PER_CELL]
            for g in shown:
                t_style  = _launch_type_style(g["type"])
                badge    = (f'<span style="font-size:11px;{t_style}">{g["type"]}</span> '
                            if g["type"] else "")
                time_pfx = (f'<span style="color:#9ca3af;font-size:11px">{g["time"]} </span>'
                            if g["time"] else "")
                items_html += (
                    f'<div style="margin-bottom:3px;line-height:1.4">'
                    f'{time_pfx}{badge}<span>{g["name"]}</span>'
                    f'</div>'
                )
            if len(games) > MAX_PER_CELL:
                extra = len(games) - MAX_PER_CELL
                items_html += f'<div style="color:#9ca3af;font-size:11px">...等{extra}款</div>'
            cells += f'<td style="{td_cell}">{items_html}</td>'
        rows_html += f"<tr>{cells}</tr>"

    table_html = f"""
    <div style="overflow:auto;max-height:700px;border:1px solid #e5e7eb;border-radius:6px">
      <table style="border-collapse:collapse;font-size:14px;table-layout:fixed">
        <thead style="position:sticky;top:0;background:#f9fafb;z-index:1">
          <tr>{header}</tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """
    st.html(table_html)
    st.caption("绿色=首发/公测，蓝色=预约，橙色=删档测试，灰色=其他")


# ── 主体 ────────────────────────────────────────────────────────────────────
if sel_page == "国内排行榜":
    if auto_refresh:
        @st.fragment(run_every=timedelta(minutes=refresh_mins))
        def auto_render():
            _db = get_db()
            latest_dates = _db.available_dates()
            active_date  = sel_date if sel_date in latest_dates else (latest_dates[0] if latest_dates else sel_date)
            render_data(active_date, sel_platform, sel_rank_type)
            st.caption(f"🕐 自动刷新中 · 上次更新: {datetime.now().strftime('%H:%M:%S')} · 间隔 {refresh_mins} 分钟")
        auto_render()
    else:
        render_data(sel_date, sel_platform, sel_rank_type)

elif sel_page == "国内开测表":
    render_launches(db, sel_date, sel_platform)

else:
    render_overseas(db, sel_date, sel_rank_type)
