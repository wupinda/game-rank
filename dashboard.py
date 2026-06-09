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

st.markdown("""
<style>
:root {
  --ap-bg:      #f5f5f7;
  --ap-card:    #ffffff;
  --ap-text:    #1d1d1f;
  --ap-sub:     #6e6e73;
  --ap-div:     #e8e8ed;
  --ap-accent:  #0071e3;
  --ap-green-bg:#e8f8ed;
  --ap-red-bg:  #fff0ef;
  --ap-blue-bg: #e8f0ff;
  --ap-shadow:  0 2px 12px rgba(0,0,0,.08);
  --ap-font:    -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}
body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
  font-family: var(--ap-font) !important;
  background: var(--ap-bg) !important;
}
[data-testid="stAppViewContainer"] > .main {
  padding-left: 0 !important;
}
[data-testid="stAppViewContainer"] > .main .block-container {
  padding-left: 0.75rem !important;
  padding-right: 2rem !important;
  max-width: 100% !important;
}
/* 针对性覆盖 Streamlit 组件字体，排除 Material Symbols 图标 */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] select,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] [data-testid],
[data-testid="stAppViewContainer"] .stMarkdown {
  font-family: var(--ap-font) !important;
}
[data-testid="stSidebar"] {
  background: var(--ap-card) !important;
  border-right: 1px solid var(--ap-div) !important;
  min-width: 200px !important;
  max-width: 200px !important;
}
[data-testid="stSidebar"] > div {
  min-width: 200px !important;
  max-width: 200px !important;
  width: 200px !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
  padding-top: 20px !important;
}
/* 针对性设置侧边栏字体，不触碰 button/span（Material Symbols 图标） */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] input {
  font-family: var(--ap-font) !important;
}
[data-testid="stSidebar"] h1 {
  font-size: 17px !important;
  font-weight: 600 !important;
  letter-spacing: -0.3px !important;
  color: var(--ap-text) !important;
}
/* 侧边栏间距：divider 收紧，只缩减 radio nav 区域上下边距 */
[data-testid="stSidebar"] hr {
  margin: 10px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] {
  margin-top: -4px !important;
  margin-bottom: -4px !important;
}
/* 立即抓取数据按钮：全宽 + 与 selectbox 对齐 */
[data-testid="stSidebar"] [data-testid="stButton"],
[data-testid="stSidebar"] [data-testid="stButton"] > button,
[data-testid="stSidebar"] .stButton,
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  display: block !important;
  box-sizing: border-box !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
  border: 1px solid #c7c7cc !important;
  border-radius: 10px !important;
  background: var(--ap-bg) !important;
  font-size: 14px !important;
}
.stButton > button {
  background: var(--ap-accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 980px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  font-family: var(--ap-font) !important;
  padding: 10px 20px !important;
  transition: opacity .15s !important;
}
.stButton > button:hover { opacity: .85 !important; }
hr { border-color: var(--ap-div) !important; }
h1, h2, h3 {
  font-family: var(--ap-font) !important;
  color: var(--ap-text) !important;
  letter-spacing: -0.5px !important;
}
h1 { font-size: 28px !important; font-weight: 700 !important; }
h2 { font-size: 20px !important; font-weight: 600 !important; }
[data-testid="stCaptionContainer"] p { color: var(--ap-sub) !important; font-size: 12px !important; }
/* Multiselect — 去掉外框 */
[data-testid="stMultiSelect"] > div,
[data-testid="stMultiSelect"] > div > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}
/* Chip 标签 */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
  background: #f5f5f7 !important;
  border: 1px solid #d2d2d7 !important;
  border-radius: 20px !important;
  color: var(--ap-text) !important;
  font-size: 12px !important;
  font-family: var(--ap-font) !important;
  padding: 3px 6px 3px 10px !important;
  margin: 2px 3px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
  color: var(--ap-text) !important;
  font-size: 12px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
  color: #8e8e93 !important;
  width: 14px !important;
  height: 14px !important;
}
/* 输入框光标区域（用于触发下拉） */
[data-testid="stMultiSelect"] input {
  font-size: 12px !important;
  color: var(--ap-accent) !important;
  min-width: 60px !important;
}
[data-testid="stMultiSelect"] input::placeholder {
  color: var(--ap-accent) !important;
  font-size: 12px !important;
}
/* 下拉菜单 */
[data-baseweb="popover"] [data-baseweb="menu"] {
  border-radius: 12px !important;
  border: 1px solid #e8e8ed !important;
  box-shadow: 0 4px 20px rgba(0,0,0,.12) !important;
  overflow: hidden !important;
}
[data-baseweb="popover"] [role="option"] {
  font-size: 14px !important;
  color: var(--ap-text) !important;
  font-family: var(--ap-font) !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {
  background: rgba(0,113,227,.08) !important;
}
/* ── Sidebar section labels (uppercase caps) ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > label,
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] > p,
[data-testid="stSidebar"] [data-testid="stSelectbox"] > label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] > p {
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.6px !important;
  color: #6e6e73 !important;
}
/* ── Sidebar radio → nav items ── */
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
  display: none !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] {
  padding: 9px 12px !important;
  border-radius: 10px !important;
  margin-bottom: 2px !important;
  cursor: pointer !important;
  transition: background .12s !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:hover {
  background: #f5f5f7 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) {
  background: rgba(0,113,227,.1) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) p {
  color: #0071e3 !important;
  font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] p {
  font-size: 14px !important;
  color: #1d1d1f !important;
  margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)

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


_AP_FONT = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"

def _dynamic_card_html(sections: list) -> str:
    """
    sections: list of dicts
      type:  'green' | 'red' | 'blue'
      icon:  emoji str
      title: str
      rows:  list of dicts  {platform, game, change, hint}
    """
    _icon_bg  = {"green": "#e8f8ed", "red": "#fff0ef", "blue": "#e8f0ff"}
    _tag_style = {
        "green": "background:#e8f8ed;color:#1a7a3a",
        "red":   "background:#fff0ef;color:#cc2200",
        "blue":  "background:#e8f0ff;color:#0055cc",
    }
    body = ""
    for i, sec in enumerate(sections):
        t   = sec["type"]
        sep = "border-top:1px solid #e8e8ed;" if i > 0 else ""
        rows_html = ""
        for row in sec["rows"]:
            chg   = row.get("change", "")
            hint  = row.get("hint", "")
            tag   = (f'<span style="display:inline-flex;align-items:center;padding:2px 8px;'
                     f'border-radius:20px;font-size:12px;font-weight:600;flex-shrink:0;'
                     f'{_tag_style[t]}">{chg}</span>') if chg else ""
            hint_tag = (f'<span style="font-size:11px;color:#6e6e73;background:#f5f5f7;'
                        f'padding:2px 7px;border-radius:20px;flex-shrink:0">{hint}</span>') if hint else ""
            rows_html += (
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;'
                f'font-family:{_AP_FONT}">'
                f'<span style="font-size:12px;color:#6e6e73;min-width:72px;flex-shrink:0">{row["platform"]}</span>'
                f'<div style="display:flex;align-items:center;gap:8px">'
                f'<span style="font-size:14px;font-weight:500;color:#1d1d1f">{row["game"]}</span>'
                f'{tag}{hint_tag}</div></div>'
            )
        body += (
            f'<div style="{sep}padding:14px 20px;display:flex;align-items:flex-start;gap:14px">'
            f'<div style="width:32px;height:32px;border-radius:8px;background:{_icon_bg[t]};'
            f'display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;margin-top:1px">'
            f'{sec["icon"]}</div>'
            f'<div style="flex:1">'
            f'<div style="font-size:13px;font-weight:600;color:#1d1d1f;margin-bottom:8px;font-family:{_AP_FONT}">'
            f'{sec["title"]}</div>{rows_html}</div></div>'
        )
    return (
        f'<div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);'
        f'overflow:hidden;margin-bottom:20px;border:1px solid #e8e8ed">'
        f'<div style="padding:14px 20px;border-bottom:1px solid #e8e8ed;font-size:13px;'
        f'font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">今日动态</div>'
        f'{body}</div>'
    )


def _static_chips_html(labels: list) -> str:
    """卡片 header 右侧的静态渠道展示（只显示，不可交互）。"""
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;'
        f'background:#f5f5f7;border:1px solid #d2d2d7;border-radius:20px;'
        f'padding:3px 10px;font-size:12px;color:#1d1d1f;'
        f'font-family:{_AP_FONT}">{lbl}</span>'
        for lbl in labels
    )
    return f'<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">{items}</div>'


def _ap_badge(chg: str) -> str:
    """返回 Apple 风格涨跌徽章 HTML。"""
    base = ("display:inline-flex;align-items:center;justify-content:center;"
            "min-width:42px;padding:2px 7px;border-radius:6px;"
            "font-size:12px;font-weight:700;flex-shrink:0")
    if chg is None:
        return ""
    if "↑" in chg:
        return f'<span style="{base};background:#e8f8ed;color:#1a7a3a">▲{chg.replace("↑","")}</span>'
    if "↓" in chg:
        return f'<span style="{base};background:#fff0ef;color:#cc2200">▼{chg.replace("↓","")}</span>'
    if chg == "NEW":
        return f'<span style="{base};background:#e8f0ff;color:#0055cc">NEW</span>'
    return '<span style="color:#d2d2d7;flex-shrink:0">—</span>'


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
st.sidebar.title("游戏排行榜")

db = get_db()

dates = db.available_dates()
if not dates:
    st.warning("数据库暂无数据，请先运行 `python main.py fetch` 抓取数据。")
    st.code("python main.py fetch", language="bash")
    st.stop()

st.sidebar.markdown(
    f'<p style="font-size:12px;color:#6e6e73;margin:-8px 0 0;'
    f'font-family:{_AP_FONT}">数据更新至 {dates[0]}</p>',
    unsafe_allow_html=True,
)
st.sidebar.divider()

# 页签导航（放最前，后续选项依赖它）
_PAGES = ["国内排行榜", "国内开测表", "海外排行榜"]
sel_page = st.sidebar.radio("页签", _PAGES, key="sel_page", label_visibility="visible")
st.sidebar.divider()

sel_date = st.sidebar.selectbox("日期", dates, index=0)

sel_platform = None

# 榜单类型——海外只显示下载榜/畅销榜/活跃榜（活跃榜仅 Steam 有）
if sel_page == "国内开测表":
    sel_rank_type = None
elif sel_page == "海外排行榜":
    _overseas_rank_opts = {"下载榜": "download", "畅销榜": "revenue", "活跃榜": "active"}
    sel_rank_label = st.sidebar.selectbox("榜单类型", list(_overseas_rank_opts.keys()))
    sel_rank_type = _overseas_rank_opts[sel_rank_label]
else:
    rank_type_labels = {"全部": None, **{v: k for k, v in RANK_TYPES.items()}}
    _rank_options = list(rank_type_labels.keys())
    _default_rank_idx = _rank_options.index("预约榜") if "预约榜" in _rank_options else 0
    sel_rank_label = st.sidebar.selectbox(
        "榜单类型",
        options=_rank_options,
        index=_default_rank_idx,
    )
    sel_rank_type = rank_type_labels[sel_rank_label]

st.sidebar.divider()
if st.sidebar.button("立即抓取数据"):
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

    st.title("国内排行榜")

    # 平台显示名 -> platform key 的映射（全量，供表格与趋势图共用）
    plt_label_to_key = {}
    if not df.empty:
        plt_label_to_key = (
            df[["platform", "平台"]].drop_duplicates()
            .set_index("平台")["platform"].to_dict()
        )

    # 多平台对比视图
    if not df.empty and sel_rank_type:
        change_map = build_rank_change_map(db, sel_date, sel_rank_type)

        _all_plt_labels = sorted(plt_label_to_key.keys())

        # ── 今日动态概述（用全量平台数据）────────────────────────────────────
        if change_map:
            from collections import Counter
            all_plt_keys = {plt_label_to_key.get(c) for c in _all_plt_labels}
            risers, fallers = [], []
            for (plt_key, game), chg in change_map.items():
                if plt_key not in all_plt_keys:
                    continue
                if "↑" in chg:
                    risers.append((int(chg.replace("↑", "")), game, plt_key))
                elif "↓" in chg:
                    fallers.append((int(chg.replace("↓", "")), game, plt_key))
            risers.sort(reverse=True)
            fallers.sort(reverse=True)
            game_plt_count = Counter()
            for (plt_key, game) in change_map.keys():
                if plt_key in all_plt_keys:
                    game_plt_count[game] += 1
            cross_plts = sorted(
                [(cnt, g) for g, cnt in game_plt_count.items() if cnt >= 3], reverse=True
            )
            sections = []
            if risers:
                rows = []
                for n, g, pk in risers[:3]:
                    a = _analyze_movement(db, g, pk, sel_rank_type, sel_date, change_map)
                    rows.append({"platform": PLATFORMS.get(pk, pk), "game": g, "change": f"▲ {n}", "hint": a})
                sections.append({"type": "green", "icon": "📈", "title": "最大涨幅", "rows": rows})
            if fallers:
                rows = []
                for n, g, pk in fallers[:3]:
                    a = _analyze_movement(db, g, pk, sel_rank_type, sel_date, change_map)
                    rows.append({"platform": PLATFORMS.get(pk, pk), "game": g, "change": f"▼ {n}", "hint": a})
                sections.append({"type": "red", "icon": "📉", "title": "最大跌幅", "rows": rows})
            if cross_plts:
                rows = [{"platform": "", "game": g, "change": f"{cnt} 个平台", "hint": ""} for cnt, g in cross_plts[:4]]
                sections.append({"type": "blue", "icon": "🔥", "title": "多平台上榜", "rows": rows})
            if sections:
                st.html(_dynamic_card_html(sections))

        # ── 渠道选择（紧贴表格上方）──────────────────────────────────────────
        _sel_plt_labels = st.multiselect(
            "展示渠道",
            options=_all_plt_labels,
            default=_all_plt_labels,
            key=f"plt_sort_{sel_date}_{sel_rank_type}",
        )

        # 根据选择过滤数据并构建 pivot
        df_view = df[df["平台"].isin(_sel_plt_labels)] if _sel_plt_labels else df
        pivot = df_view.pivot_table(
            index="排名", columns="平台", values="游戏名", aggfunc="first"
        ).reset_index()
        game_cols = [c for c in _sel_plt_labels if c in pivot.columns]

        # 构建 HTML 表格（Apple 风格）
        DIVIDER = "border-right:1px solid #e8e8ed"
        COL_W   = "width:220px;min-width:220px;max-width:220px"
        th_base = (f"padding:10px 14px;border-bottom:1px solid #e8e8ed;font-size:11px;"
                   f"font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:#6e6e73;{COL_W};{DIVIDER}")
        th_rank = (f"padding:10px 10px;border-bottom:1px solid #e8e8ed;text-align:center;"
                   f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;"
                   f"color:#6e6e73;width:52px;min-width:52px;{DIVIDER}")

        header = f'<th style="{th_rank}">排名</th>' + "".join(
            f'<th style="{th_base}">{col}</th>' for col in game_cols
        )

        rows_html = ""
        for _, row in pivot.iterrows():
            rank_val = int(row["排名"])
            td_rank = (f"padding:10px 10px;text-align:center;color:#6e6e73;font-size:13px;"
                       f"width:52px;{DIVIDER};border-bottom:1px solid #e8e8ed;background:#fff")
            td_game = f"padding:10px 12px;{COL_W};{DIVIDER};border-bottom:1px solid #e8e8ed;background:#fff"
            cells = f'<td style="{td_rank}">{rank_val}</td>'
            for col in game_cols:
                game = row.get(col)
                if game is None or (isinstance(game, float) and pd.isna(game)):
                    cells += f'<td style="{td_game}"></td>'
                    continue
                plt_key = plt_label_to_key.get(col, "")
                chg   = change_map.get((plt_key, game), None) if change_map else None
                badge = _ap_badge(chg)
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="overflow:hidden;text-overflow:ellipsis">{game}</span>'
                    f'{badge}</div>'
                )
                cells += f'<td style="{td_game}">{cell_inner}</td>'
            rows_html += f'<tr class="ap-tr">{cells}</tr>'

        title_str = f'{RANK_TYPES.get(sel_rank_type, sel_rank_type)} — Top 20 对比'
        table_html = f"""
        <style>
          .ap-tbl .ap-tr:hover td {{ background: rgba(0,113,227,.05) !important; }}
          .ap-tbl .ap-tr:last-child td {{ border-bottom: none !important; }}
        </style>
        <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                    overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
          <div style="padding:14px 20px;border-bottom:1px solid #e8e8ed">
            <span style="font-size:13px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">
              {title_str}
            </span>
          </div>
          <div style="overflow:auto;max-height:600px">
            <table class="ap-tbl" style="border-collapse:collapse;font-size:14px;
                   table-layout:fixed;font-family:{_AP_FONT};width:100%">
              <thead style="position:sticky;top:0;background:#fff;z-index:1">
                <tr>{header}</tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
          <div style="border-top:1px solid #e8e8ed;padding:10px 20px;font-size:12px;
                      color:#6e6e73;font-family:{_AP_FONT}">
            ▲▼ 与前一日排名对比，NEW 表示新上榜，— 表示未变化
          </div>
        </div>
        """
        st.html(table_html)

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
    st.subheader("排名趋势")
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
    st.title("海外排行榜")

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

    # HTML table（Apple 风格）
    _DIVIDER = "border-right:1px solid #e8e8ed"
    _COL_W   = "width:220px;min-width:220px;max-width:220px"
    _th_rank = (f"padding:10px 10px;border-bottom:1px solid #e8e8ed;text-align:center;"
                f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;"
                f"color:#6e6e73;width:52px;min-width:52px;{_DIVIDER}")
    _th_game = (f"padding:10px 14px;border-bottom:1px solid #e8e8ed;font-size:11px;"
                f"font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:#6e6e73;{_COL_W};{_DIVIDER}")

    def _render_table(rank_maps, plt_keys, plt_lbls, max_rank, section_title=""):
        header = f'<th style="{_th_rank}">排名</th>' + "".join(
            f'<th style="{_th_game}">{lbl}</th>' for lbl in plt_lbls
        )
        rows_html = ""
        for rank_val in range(1, min(max_rank, 30) + 1):
            td_rank = (f"padding:10px 10px;text-align:center;color:#6e6e73;font-size:13px;"
                       f"width:52px;{_DIVIDER};border-bottom:1px solid #e8e8ed;background:#fff")
            td_game = f"padding:10px 12px;{_COL_W};{_DIVIDER};border-bottom:1px solid #e8e8ed;background:#fff"
            cells   = f'<td style="{td_rank}">{rank_val}</td>'
            for plt_key in plt_keys:
                game = rank_maps[plt_key].get(rank_val)
                if not game:
                    cells += f'<td style="{td_game}"></td>'
                    continue
                chg   = change_map.get((plt_key, game), None) if change_map else None
                badge = _ap_badge(chg)
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="overflow:hidden;text-overflow:ellipsis">{game}</span>'
                    f'{badge}</div>'
                )
                cells += f'<td style="{td_game}">{cell_inner}</td>'
            rows_html += f'<tr class="ap-tr">{cells}</tr>'
        card_hdr = (
            f'<div style="padding:14px 20px;border-bottom:1px solid #e8e8ed">'
            f'<span style="font-size:13px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">'
            f'{section_title}</span></div>'
        ) if section_title else ""
        caption = (
            f'<div style="border-top:1px solid #e8e8ed;padding:10px 20px;font-size:12px;'
            f'color:#6e6e73;font-family:{_AP_FONT}">'
            f'▲▼ 与前一日排名对比，NEW 表示新上榜，— 表示未变化</div>'
        ) if change_map else ""
        return f"""
        <style>
          .ap-tbl .ap-tr:hover td {{ background: rgba(0,113,227,.05) !important; }}
          .ap-tbl .ap-tr:last-child td {{ border-bottom: none !important; }}
        </style>
        <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                    overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
          {card_hdr}
          <div style="overflow:auto;max-height:600px">
            <table class="ap-tbl" style="border-collapse:collapse;font-size:14px;
                   table-layout:fixed;font-family:{_AP_FONT};width:100%">
              <thead style="position:sticky;top:0;background:#fff;z-index:1">
                <tr>{header}</tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
          {caption}
        </div>
        """

    def _render_summary(plt_keys, section_date):
        """在表格上方渲染今日动态概述（Apple 风格 HTML 卡片）"""
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
        sections = []
        if risers:
            rows = []
            for n, g, pk in risers[:3]:
                a = _analyze_movement(db, g, pk, rank_type_ov, active_date, change_map)
                rows.append({"platform": PLATFORMS.get(pk, pk), "game": g, "change": f"▲ {n}", "hint": a})
            sections.append({"type": "green", "icon": "📈", "title": "最大涨幅", "rows": rows})
        if fallers:
            rows = []
            for n, g, pk in fallers[:3]:
                a = _analyze_movement(db, g, pk, rank_type_ov, active_date, change_map)
                rows.append({"platform": PLATFORMS.get(pk, pk), "game": g, "change": f"▼ {n}", "hint": a})
            sections.append({"type": "red", "icon": "📉", "title": "最大跌幅", "rows": rows})
        if cross_plts:
            rows = [{"platform": "", "game": g, "change": f"{cnt} 个平台", "hint": ""} for cnt, g in cross_plts[:4]]
            sections.append({"type": "blue", "icon": "🔥", "title": "多平台上榜", "rows": rows})

        if sections:
            st.html(_dynamic_card_html(sections))

    if present_plts:
        _mob_labels_all = [PLATFORMS.get(k, k) for k in present_plts]
        _mob_lbl_to_key = {PLATFORMS.get(k, k): k for k in present_plts}

        _render_summary(set(present_plts), active_date)

        _sel_mob_labels = st.multiselect(
            "展示渠道",
            options=_mob_labels_all,
            default=_mob_labels_all,
            key=f"mob_plt_sort_{active_date}_{rank_type_ov}",
        )
        present_plts = [_mob_lbl_to_key[l] for l in _sel_mob_labels if l in _mob_lbl_to_key]
        plt_labels = _sel_mob_labels

        rank_maps: dict[str, dict[int, str]] = {
            k: {r["rank_pos"]: r["game_name"] for r in plt_data[k]} for k in present_plts
        }
        max_rank = max((max(rm.keys()) for rm in rank_maps.values() if rm), default=20)
        st.html(_render_table(rank_maps, present_plts, plt_labels, max_rank, section_title="移动平台排行榜"))
    else:
        st.info("移动平台暂无该榜单数据。")

    # ── PC 平台排行榜 ─────────────────────────────────────────────────────────
    pc_plts = pc_plts_pre
    pc_data = pc_data_pre

    if not pc_plts:
        st.info(f"当前日期 {active_date} 暂无 PC 平台数据，请先抓取。")
        st.code("python main.py fetch --platform steam epicgames msstore", language="bash")
    else:
        _pc_labels_all = [PLATFORMS.get(k, k) for k in pc_plts]
        _pc_lbl_to_key = {PLATFORMS.get(k, k): k for k in pc_plts}

        _render_summary(set(pc_plts), active_date)

        _sel_pc_labels = st.multiselect(
            "展示渠道",
            options=_pc_labels_all,
            default=_pc_labels_all,
            key=f"pc_plt_sort_{active_date}_{rank_type_ov}",
        )
        pc_plts = [_pc_lbl_to_key[l] for l in _sel_pc_labels if l in _pc_lbl_to_key]
        pc_labels = _sel_pc_labels

        pc_rank_maps: dict[str, dict[int, str]] = {
            k: {r["rank_pos"]: r["game_name"] for r in pc_data[k]} for k in pc_plts
        }
        pc_max_rank = max((max(rm.keys()) for rm in pc_rank_maps.values() if rm), default=20)
        st.html(_render_table(pc_rank_maps, pc_plts, pc_labels, pc_max_rank, section_title="PC 平台排行榜"))


_LAUNCH_TYPE_STYLE = {
    "首发":   "background:#e8f8ed;color:#1a7a3a",
    "公测":   "background:#e8f8ed;color:#1a7a3a",
    "不删档": "background:#e8f8ed;color:#1a7a3a",
    "预约":   "background:#e8f0ff;color:#0055cc",
    "删档":   "background:#fff3e0;color:#9a4f00",
    "测试":   "background:#fff3e0;color:#9a4f00",
}

def _launch_type_style(t: str) -> str:
    for k, v in _LAUNCH_TYPE_STYLE.items():
        if k in t:
            return v
    return "background:#f5f5f7;color:#6e6e73"

_LAUNCH_PLT_ORDER = ["bilibili", "taptap", "kuaibao", "wegame"]

def render_launches(db: Database, sel_date: str, sel_platform=None):
    launch_dates = db.available_launch_dates()
    if not launch_dates:
        st.info("暂无开测数据，请先运行 `python main.py fetch` 抓取数据。")
        st.code("python main.py fetch", language="bash")
        return

    active_date = sel_date if sel_date in launch_dates else launch_dates[0]
    rows = db.query_launches(fetch_date=active_date)

    st.title("国内开测表")

    if not rows:
        st.info(f"当前日期 {active_date} 暂无开测数据。")
        return

    df = pd.DataFrame(rows)
    from datetime import date as _date_cls
    from collections import defaultdict
    today_str = _date_cls.today().isoformat()

    df["_plt_label"] = df["platform"].map(lambda x: PLATFORMS.get(x, x))
    df["_date"]      = df["launch_time"].str[:10].apply(
        lambda x: x if (x and len(x) == 10) else "待定"
    )
    df["_time"]      = df["launch_time"].str[11:16]

    # 确定渠道列顺序
    present_plts = set(df["platform"].unique())
    plt_keys  = [k for k in _LAUNCH_PLT_ORDER if k in present_plts]
    plt_keys += [k for k in present_plts if k not in _LAUNCH_PLT_ORDER]
    _all_launch_labels = [PLATFORMS.get(k, k) for k in plt_keys]
    _lbl_to_key = {PLATFORMS.get(k, k): k for k in plt_keys}

    plt_labels = st.multiselect(
        "展示渠道",
        options=_all_launch_labels,
        default=_all_launch_labels,
        key=f"launch_plt_sort_{active_date}",
    )
    plt_keys = [_lbl_to_key[l] for l in plt_labels if l in _lbl_to_key]

    # 按 (日期, 渠道) 聚合游戏列表
    cell_map  = defaultdict(lambda: defaultdict(list))
    dates_set = set()
    for _, r in df.iterrows():
        dates_set.add(r["_date"])
        cell_map[r["_date"]][r["_plt_label"]].append({
            "name": r["game_name"],
            "type": r["launch_type"],
            "time": r["_time"],
        })

    sorted_dates = (
        sorted(d for d in dates_set if d != "待定" and d >= today_str)
        + (["待定"] if "待定" in dates_set else [])
    )

    # HTML 表格（Apple 风格）
    DIVIDER = "border-right:1px solid #e8e8ed"
    TIME_W  = "width:100px;min-width:100px"
    COL_W   = "width:220px;min-width:220px;max-width:220px"
    th_time = (f"padding:10px 10px;border-bottom:1px solid #e8e8ed;font-size:11px;font-weight:600;"
               f"text-transform:uppercase;letter-spacing:0.5px;color:#6e6e73;{TIME_W};{DIVIDER}")
    th_plt  = (f"padding:10px 14px;border-bottom:1px solid #e8e8ed;font-size:11px;font-weight:600;"
               f"text-transform:uppercase;letter-spacing:0.5px;color:#6e6e73;{COL_W};{DIVIDER}")
    td_time = (f"padding:10px 10px;border-bottom:1px solid #e8e8ed;vertical-align:top;"
               f"color:#6e6e73;font-size:13px;font-family:{_AP_FONT};{TIME_W};{DIVIDER}")
    td_cell = (f"padding:10px 12px;border-bottom:1px solid #e8e8ed;vertical-align:top;"
               f"font-family:{_AP_FONT};{COL_W};{DIVIDER}")

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
            for g in games[:MAX_PER_CELL]:
                t_style  = _launch_type_style(g["type"])
                badge    = (
                    f'<span style="display:inline-block;padding:1px 7px;border-radius:20px;'
                    f'font-size:11px;font-weight:500;margin-right:4px;{t_style}">{g["type"]}</span>'
                    if g["type"] else ""
                )
                time_pfx = (
                    f'<span style="color:#6e6e73;font-size:11px;margin-right:3px">{g["time"]}</span>'
                    if g["time"] else ""
                )
                items_html += (
                    f'<div style="display:flex;align-items:baseline;gap:4px;'
                    f'margin-bottom:5px;line-height:1.4">'
                    f'{time_pfx}{badge}'
                    f'<span style="font-size:13px;color:#1d1d1f">{g["name"]}</span>'
                    f'</div>'
                )
            if len(games) > MAX_PER_CELL:
                extra = len(games) - MAX_PER_CELL
                items_html += (f'<div style="color:#6e6e73;font-size:11px;margin-top:2px">'
                               f'另有 {extra} 款</div>')
            cells += f'<td style="{td_cell}">{items_html}</td>'
        rows_html += f'<tr class="lch-tr">{cells}</tr>'

    table_html = f"""
    <style>
      .lch-tbl .lch-tr:hover td {{ background: rgba(0,113,227,.04) !important; }}
      .lch-tbl .lch-tr:last-child td {{ border-bottom: none !important; }}
    </style>
    <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
      <div style="padding:14px 20px;border-bottom:1px solid #e8e8ed">
        <span style="font-size:13px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">
          近期开测信息 — {active_date}
        </span>
      </div>
      <div style="overflow:auto;max-height:700px">
        <table class="lch-tbl" style="border-collapse:collapse;font-size:14px;
               table-layout:fixed;font-family:{_AP_FONT}">
          <thead style="position:sticky;top:0;background:#fff;z-index:1">
            <tr>{header}</tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
      <div style="border-top:1px solid #e8e8ed;padding:10px 20px;font-size:12px;
                  color:#6e6e73;font-family:{_AP_FONT};display:flex;gap:12px;flex-wrap:wrap">
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
              background:#34c759;margin-right:4px"></span>首发 / 公测</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
              background:#0071e3;margin-right:4px"></span>预约</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
              background:#ff9500;margin-right:4px"></span>删档 / 测试</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
              background:#8e8e93;margin-right:4px"></span>其他</span>
      </div>
    </div>
    """
    st.html(table_html)


# ── 主体 ────────────────────────────────────────────────────────────────────
if sel_page == "国内排行榜":
    render_data(sel_date, sel_platform, sel_rank_type)

elif sel_page == "国内开测表":
    render_launches(db, sel_date, sel_platform)

else:
    render_overseas(db, sel_date, sel_rank_type)
