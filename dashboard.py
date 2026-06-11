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
  --ap-bg:      #ffffff;
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
/* 立即抓取数据按钮：与 selectbox 等宽 */
[data-testid="stSidebar"] [data-testid="stButton"] > button,
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  box-sizing: border-box !important;
  padding: 10px 20px !important;
  border-radius: 980px !important;
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
/* Multiselect 容器 */
[data-testid="stMultiSelect"] > div,
[data-testid="stMultiSelect"] > div > div {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"] {
  background: var(--ap-bg) !important;
  border: 1px solid #e8e8ed !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.06) !important;
  padding: 5px 8px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within {
  border-color: #a0a0a5 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
}
/* Chip — Apple 系统灰 */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
  background: #ebebf0 !important;
  border: none !important;
  border-radius: 100px !important;
  color: #1d1d1f !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  font-family: var(--ap-font) !important;
  padding: 2px 6px 2px 10px !important;
  margin: 2px 3px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
  color: #1d1d1f !important;
  font-size: 12px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {
  color: #6e6e73 !important;
  width: 12px !important;
  height: 12px !important;
}
/* 输入框 */
[data-testid="stMultiSelect"] input {
  font-size: 13px !important;
  color: var(--ap-text) !important;
  min-width: 40px !important;
}
[data-testid="stMultiSelect"] input::placeholder {
  color: #aeaeb2 !important;
  font-size: 13px !important;
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
    "appgallery", "galaxystore", "getapps", "amazon",
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


@st.cache_data(ttl=300)
def _cached_query(_db, platform=None, rank_type=None, fetch_date=None):
    return _db.query(platform=platform, rank_type=rank_type, fetch_date=fetch_date)


@st.cache_data(ttl=300)
def _cached_dates(_db):
    return _db.available_dates()


@st.cache_data(ttl=300)
def _cached_trend(_db, game_name, platform, rank_type):
    return _db.trend(game_name, platform, rank_type)


def load_data(db: Database, platform=None, rank_type=None, fetch_date=None) -> pd.DataFrame:
    rows = _cached_query(db, platform=platform, rank_type=rank_type, fetch_date=fetch_date)
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
    return f'<span style="{base};background:transparent;color:#b0b0b5;font-size:14px;font-weight:700;line-height:1">—</span>'


def build_rank_change_map(db: Database, sel_date: str, rank_type: str) -> dict:
    """返回 {(platform, game_name): change_str}，无前日数据时返回空 dict。"""
    dates = _cached_dates(db)
    if sel_date not in dates:
        return {}
    idx = dates.index(sel_date)
    if idx + 1 >= len(dates):
        return {}
    prev_date = dates[idx + 1]
    prev_rows = _cached_query(db, rank_type=rank_type, fetch_date=prev_date)
    prev_lookup = {(r["platform"], r["game_name"]): r["rank_pos"] for r in prev_rows}
    curr_rows = _cached_query(db, rank_type=rank_type, fetch_date=sel_date)
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
    dates = _cached_dates(db)
    if sel_date not in dates:
        return ""
    idx = dates.index(sel_date)

    history = []
    for i in range(min(5, idx + 1)):
        rows = _cached_query(db, platform=plt_key, rank_type=rank_type, fetch_date=dates[idx + i])
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

dates = _cached_dates(db)
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
_PAGES = ["国内排行榜", "国内开测表", "海外排行榜-移动", "海外排行榜-PC", "竞品监控"]
sel_page = st.sidebar.radio("页签", _PAGES, key="sel_page", label_visibility="visible")
st.sidebar.divider()

sel_date = st.sidebar.selectbox("日期", dates, index=0)

sel_platform = None

# 榜单类型——海外只显示下载榜/畅销榜/活跃榜（活跃榜仅 Steam 有）
if sel_page in ("竞品监控",):
    sel_rank_type = None
elif sel_page == "国内开测表":
    sel_rank_type = None
elif sel_page in ("海外排行榜-移动", "海外排行榜-PC"):
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
        _fetch_env = {**os.environ}
        try:
            _fetch_env["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
            _fetch_env["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]
        except Exception:
            pass  # 本地运行时 secrets 不存在，依赖 config.yaml 或已有环境变量
        result = subprocess.run(
            [sys.executable, "main.py", "fetch"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=_fetch_env,
        )
    if result.returncode == 0:
        st.sidebar.success("抓取完成！")
        st.rerun()
    else:
        st.sidebar.error(f"抓取失败：{result.stderr[:500]}")


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

        _key_to_label = {v: k for k, v in plt_label_to_key.items()}
        _all_plt_labels = (
            [_key_to_label[k] for k in _DOMESTIC_PLT_ORDER if k in _key_to_label]
            + [l for l in plt_label_to_key if l not in
               {_key_to_label[k] for k in _DOMESTIC_PLT_ORDER if k in _key_to_label}]
        )

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

        # ── 渠道选择：先从 session_state 读取，multiselect 放在表格下方 ──────
        _plt_key = f"plt_sort_{sel_date}_{sel_rank_type}"
        _sel_plt_labels = st.session_state.get(_plt_key, _all_plt_labels)
        if not _sel_plt_labels:
            _sel_plt_labels = _all_plt_labels

        # 根据选择过滤数据并构建 pivot
        df_view = df[df["平台"].isin(_sel_plt_labels)] if _sel_plt_labels else df
        pivot = df_view.pivot_table(
            index="排名", columns="平台", values="游戏名", aggfunc="first"
        ).reset_index()
        game_cols = [c for c in _sel_plt_labels if c in pivot.columns]

        # ── 搜索框 ──────────────────────────────────────────────────────────
        search_query = st.text_input(
            "", placeholder="搜索游戏名...",
            key=f"search_dom_{sel_date}_{sel_rank_type}",
            label_visibility="collapsed",
        )

        # 构建 HTML 表格（Apple 风格，无竖线）
        COL_W   = "width:220px;min-width:220px;max-width:220px"
        th_style = (f"padding:10px 16px;border-bottom:1px solid #f2f2f7;text-align:left;"
                    f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;"
                    f"color:#6e6e73;background:#fff")
        th_base = f"{th_style};{COL_W}"
        th_rank = f"{th_style};width:56px;min-width:56px"

        header = f'<th style="{th_rank}">排名</th>' + "".join(
            f'<th style="{th_base}">{col}</th>' for col in game_cols
        )

        match_count = 0
        rows_html = ""
        for _, row in pivot.iterrows():
            rank_val = int(row["排名"])
            td_rank = (f"padding:11px 16px;text-align:left;color:#1d1d1f;font-size:14px;"
                       f"font-weight:600;width:56px;border-bottom:1px solid #f2f2f7")
            td_game = f"padding:11px 16px;{COL_W};border-bottom:1px solid #f2f2f7"
            cells = f'<td style="{td_rank}">{rank_val}</td>'
            for col in game_cols:
                game = row.get(col)
                if game is None or (isinstance(game, float) and pd.isna(game)):
                    cells += f'<td style="{td_game}"><span style="color:#c7c7cc">—</span></td>'
                    continue
                plt_key = plt_label_to_key.get(col, "")
                chg   = change_map.get((plt_key, game), None) if change_map else None
                badge = _ap_badge(chg)
                _is_match = bool(search_query) and search_query.lower() in str(game).lower()
                if _is_match:
                    match_count += 1
                _td = td_game + (";background-color:#fff3cd" if _is_match else "")
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="color:#1d1d1f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{game}</span>'
                    f'{badge}</div>'
                )
                cells += f'<td style="{_td}">{cell_inner}</td>'
            rows_html += f'<tr class="ap-tr">{cells}</tr>'

        title_str = f'{RANK_TYPES.get(sel_rank_type, sel_rank_type)} — Top 20 对比'
        table_html = f"""
        <style>
          .ap-tbl .ap-tr:hover td {{ background: #f5f5f7 !important; }}
          .ap-tbl .ap-tr:last-child td {{ border-bottom: none !important; }}
        </style>
        <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                    overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
          <div style="padding:16px 20px;border-bottom:1px solid #f2f2f7">
            <span style="font-size:14px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">
              {title_str}
            </span>
          </div>
          <div style="overflow:auto;max-height:600px">
            <table class="ap-tbl" style="border-collapse:collapse;font-size:14px;
                   table-layout:fixed;font-family:{_AP_FONT};width:auto">
              <thead style="position:sticky;top:0;z-index:1">
                <tr>{header}</tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
          <div style="border-top:1px solid #f2f2f7;padding:10px 20px;font-size:12px;
                      color:#aeaeb2;font-family:{_AP_FONT}">
            ▲▼ 与前一日排名对比，NEW 表示新上榜，— 表示未变化
          </div>
        </div>
        """
        if search_query:
            if match_count:
                st.caption(f"找到 {match_count} 处匹配")
            else:
                st.warning(f"未找到包含「{search_query}」的游戏")
        st.html(table_html)

        # ── 渠道选择（表格下方）──────────────────────────────────────────────
        st.multiselect(
            "展示渠道",
            options=_all_plt_labels,
            default=_all_plt_labels,
            key=_plt_key,
        )

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
                    for r in _cached_query(
                        db,
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
            sel_game = st.selectbox(
                "选择游戏",
                options=game_options,
                index=None,
                placeholder="输入游戏名搜索…",
            )
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
            trend_rows = _cached_trend(db, sel_game, _trend_plt_key, sel_rank_type)
            if len(trend_rows) > 1:
                tdf = pd.DataFrame(trend_rows)
                tdf.columns = ["日期", "排名"]
                fig = px.line(
                    tdf, x="日期", y="排名", markers=True,
                    title=f"{sel_game} 排名趋势（{sel_trend_plt_label} · {RANK_TYPES.get(sel_rank_type, sel_rank_type)}）",
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_xaxes(dtick=86400000, tickformat="%m/%d")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("需要多天数据才能显示趋势图，请继续每日抓取。")
        else:
            st.info("请选择游戏和平台后查看趋势。")


_DOMESTIC_PLT_ORDER = [
    "appstore", "taptap", "bilibili", "kuaibao",
    "appgallery_cn", "xiaomi", "myapp", "wegame",
]

_OVERSEAS_PLT_ORDER = [
    "appstore_us", "googleplay_us",
    "rustore", "appgallery", "galaxystore", "getapps", "amazon",
    "appstore_jp", "appstore_kr", "appstore_gb",
    "googleplay_jp", "googleplay_kr", "googleplay_gb",
]
_PC_PLT_ORDER = [
    "steam_us", "epicgames", "msstore_us",
    "steam_jp", "steam_kr", "steam_gb",
    "msstore_jp", "msstore_kr", "msstore_gb",
]
_OVERSEAS_RANK_TYPES = {"download", "revenue", "active"}

def render_overseas(db: Database, sel_date: str, sel_rank_type: str, section: str = "mobile"):
    st.title("海外排行榜 · 移动" if section == "mobile" else "海外排行榜 · PC")

    overseas_dates = _cached_dates(db)
    if not overseas_dates:
        st.info("暂无海外数据，请先运行 `python main.py fetch` 抓取数据。")
        st.code("python main.py fetch", language="bash")
        return

    active_date = sel_date if sel_date in overseas_dates else overseas_dates[0]

    # 海外只有下载榜/畅销榜，若侧边栏选了不支持的类型则回落到下载榜
    rank_type_ov = sel_rank_type if sel_rank_type in _OVERSEAS_RANK_TYPES else "download"

    # One batch query for all overseas platforms, then group by platform in Python
    _all_rows = _cached_query(db, rank_type=rank_type_ov, fetch_date=active_date)
    _all_grouped: dict[str, list] = {}
    for _r in _all_rows:
        _all_grouped.setdefault(_r["platform"], []).append(_r)

    present_plts = [k for k in _OVERSEAS_PLT_ORDER if _all_grouped.get(k)]
    plt_data: dict[str, list] = {k: _all_grouped[k] for k in present_plts}

    pc_plts_pre = [k for k in _PC_PLT_ORDER if _all_grouped.get(k)]
    pc_data_pre: dict[str, list] = {k: _all_grouped[k] for k in pc_plts_pre}

    if not present_plts and not pc_plts_pre:
        st.info(f"当前日期 {active_date} 暂无海外数据，请先抓取。")
        return

    # Build change map (compared to previous day) — reuse existing util
    change_map = build_rank_change_map(db, active_date, rank_type_ov)

    # HTML table（Apple 风格，无竖线）
    _COL_W   = "width:220px;min-width:220px;max-width:220px"
    _th_style = (f"padding:10px 16px;border-bottom:1px solid #f2f2f7;text-align:left;"
                 f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;"
                 f"color:#6e6e73;background:#fff")
    _th_rank = f"{_th_style};width:56px;min-width:56px"
    _th_game = f"{_th_style};{_COL_W}"

    def _render_table(rank_maps, plt_keys, plt_lbls, max_rank, section_title="", search=""):
        header = f'<th style="{_th_rank}">排名</th>' + "".join(
            f'<th style="{_th_game}">{lbl}</th>' for lbl in plt_lbls
        )
        rows_html = ""
        for rank_val in range(1, min(max_rank, 30) + 1):
            td_rank = (f"padding:11px 16px;text-align:left;color:#1d1d1f;font-size:14px;"
                       f"font-weight:600;width:56px;border-bottom:1px solid #f2f2f7")
            td_game = f"padding:11px 16px;{_COL_W};border-bottom:1px solid #f2f2f7"
            cells   = f'<td style="{td_rank}">{rank_val}</td>'
            for plt_key in plt_keys:
                game = rank_maps[plt_key].get(rank_val)
                if not game:
                    cells += f'<td style="{td_game}"><span style="color:#c7c7cc">—</span></td>'
                    continue
                chg   = change_map.get((plt_key, game), None) if change_map else None
                badge = _ap_badge(chg)
                _is_match = bool(search) and search.lower() in game.lower()
                _td = td_game + (";background-color:#fff3cd" if _is_match else "")
                cell_inner = (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
                    f'<span style="color:#1d1d1f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{game}</span>'
                    f'{badge}</div>'
                )
                cells += f'<td style="{_td}">{cell_inner}</td>'
            rows_html += f'<tr class="ap-tr">{cells}</tr>'
        card_hdr = (
            f'<div style="padding:16px 20px;border-bottom:1px solid #f2f2f7">'
            f'<span style="font-size:14px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">'
            f'{section_title}</span></div>'
        ) if section_title else ""
        caption = (
            f'<div style="border-top:1px solid #f2f2f7;padding:10px 20px;font-size:12px;'
            f'color:#aeaeb2;font-family:{_AP_FONT}">'
            f'▲▼ 与前一日排名对比，NEW 表示新上榜，— 表示未变化</div>'
        ) if change_map else ""
        return f"""
        <style>
          .ap-tbl .ap-tr:hover td {{ background: #f5f5f7 !important; }}
          .ap-tbl .ap-tr:last-child td {{ border-bottom: none !important; }}
        </style>
        <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                    overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
          {card_hdr}
          <div style="overflow:auto;max-height:600px">
            <table class="ap-tbl" style="border-collapse:collapse;font-size:14px;
                   table-layout:fixed;font-family:{_AP_FONT};width:auto">
              <thead style="position:sticky;top:0;z-index:1">
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

    def _render_section(plts, data, key_prefix):
        """渲染单个海外区块：今日动态 → 排行表 → 展示渠道（表格下方）→ 排名趋势"""
        labels_all  = [PLATFORMS.get(k, k) for k in plts]
        lbl_to_key  = {PLATFORMS.get(k, k): k for k in plts}

        _render_summary(set(plts), active_date)

        # session_state 模式：先读取上次选择，multiselect 渲染在表格之后
        _ms_key = f"{key_prefix}_{active_date}_{rank_type_ov}"
        _sel_labels = st.session_state.get(_ms_key, labels_all)
        if not _sel_labels:
            _sel_labels = labels_all
        active_plts  = [lbl_to_key[l] for l in _sel_labels if l in lbl_to_key]
        active_labels = _sel_labels

        rank_maps = {k: {r["rank_pos"]: r["game_name"] for r in data[k]} for k in active_plts}
        max_rank  = max((max(rm.keys()) for rm in rank_maps.values() if rm), default=20)

        # ── 搜索框 ──────────────────────────────────────────────────────────
        _sq_key = f"{key_prefix}_search_{active_date}_{rank_type_ov}"
        search_query = st.text_input(
            "", placeholder="搜索游戏名...",
            key=_sq_key,
            label_visibility="collapsed",
        )
        if search_query:
            _match_count = sum(
                1 for k in active_plts for r in data[k]
                if search_query.lower() in r["game_name"].lower()
            )
            if _match_count:
                st.caption(f"找到 {_match_count} 处匹配")
            else:
                st.warning(f"未找到包含「{search_query}」的游戏")

        st.html(_render_table(rank_maps, active_plts, active_labels, max_rank, search=search_query))

        # 展示渠道（表格下方）
        st.multiselect("展示渠道", options=labels_all, default=labels_all, key=_ms_key)

        # 排名趋势
        st.divider()
        st.subheader("排名趋势")
        all_games = sorted({
            r["game_name"] for k in active_plts for r in data[k]
        })
        if all_games:
            tr_c1, tr_c2 = st.columns([3, 1])
            with tr_c1:
                sel_game = st.selectbox(
                    "选择游戏",
                    options=all_games,
                    index=None,
                    placeholder="输入游戏名搜索…",
                    key=f"{key_prefix}_game_{active_date}_{rank_type_ov}",
                )
            with tr_c2:
                _trend_plt_labels = sorted({
                    PLATFORMS.get(k, k) for k in active_plts
                    if any(r["game_name"] == sel_game for r in data[k])
                }) if sel_game else []
                sel_trend_plt_label = (
                    st.selectbox(
                        "选择平台", _trend_plt_labels,
                        key=f"{key_prefix}_plt_{active_date}_{rank_type_ov}",
                    )
                    if _trend_plt_labels else None
                )
            _trend_plt_key = lbl_to_key.get(sel_trend_plt_label, "") if sel_trend_plt_label else ""
            if sel_game and _trend_plt_key:
                trend_rows = _cached_trend(db, sel_game, _trend_plt_key, rank_type_ov)
                if len(trend_rows) > 1:
                    tdf = pd.DataFrame(trend_rows)
                    tdf.columns = ["日期", "排名"]
                    fig = px.line(
                        tdf, x="日期", y="排名", markers=True,
                        title=f"{sel_game} 排名趋势（{sel_trend_plt_label} · {RANK_TYPES.get(rank_type_ov, rank_type_ov)}）",
                    )
                    fig.update_yaxes(autorange="reversed")
                    fig.update_xaxes(dtick=86400000, tickformat="%m/%d")
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("需要多天数据才能显示趋势图，请继续每日抓取。")
            else:
                st.info("请选择游戏和平台后查看趋势。")

    if section == "mobile":
        if present_plts:
            _render_section(present_plts, plt_data, "mob_plt_sort")
        else:
            st.info("移动平台暂无该榜单数据。")

    else:  # section == "pc"
        if not pc_plts_pre:
            st.info(f"当前日期 {active_date} 暂无 PC 平台数据，请先抓取。")
            st.code("python main.py fetch --platform steam_us epicgames msstore_us", language="bash")
        else:
            _render_section(pc_plts_pre, pc_data_pre, "pc_plt_sort")


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

    _lch_key = f"launch_plt_sort_{active_date}"
    plt_labels = st.session_state.get(_lch_key, _all_launch_labels) or _all_launch_labels
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

    # HTML 表格（无竖线，与排行榜一致）
    TIME_W  = "width:110px;min-width:110px"
    COL_W   = "width:220px;min-width:220px;max-width:220px"
    th_style = (f"padding:10px 16px;border-bottom:1px solid #f2f2f7;text-align:left;"
                f"font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;"
                f"color:#6e6e73;background:#fff")
    th_time = f"{th_style};{TIME_W}"
    th_plt  = f"{th_style};{COL_W}"
    td_time = (f"padding:12px 16px;border-bottom:1px solid #f2f2f7;vertical-align:top;"
               f"color:#6e6e73;font-size:13px;font-weight:600;font-family:{_AP_FONT};{TIME_W}")
    td_cell = (f"padding:12px 16px;border-bottom:1px solid #f2f2f7;vertical-align:top;"
               f"font-family:{_AP_FONT};{COL_W}")

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
                    f'<span style="display:inline-block;padding:1px 7px;border-radius:100px;'
                    f'font-size:11px;font-weight:500;margin-right:5px;white-space:nowrap;flex-shrink:0;{t_style}">{g["type"]}</span>'
                    if g["type"] else ""
                )
                time_pfx = (
                    f'<span style="color:#aeaeb2;font-size:11px;margin-right:3px">{g["time"]}</span>'
                    if g["time"] else ""
                )
                items_html += (
                    f'<div style="display:flex;align-items:baseline;gap:4px;'
                    f'margin-bottom:6px;line-height:1.4">'
                    f'{time_pfx}{badge}'
                    f'<span style="font-size:14px;color:#1d1d1f">{g["name"]}</span>'
                    f'</div>'
                )
            if len(games) > MAX_PER_CELL:
                extra = len(games) - MAX_PER_CELL
                items_html += (f'<div style="color:#aeaeb2;font-size:11px;margin-top:2px">'
                               f'另有 {extra} 款</div>')
            cells += f'<td style="{td_cell}">{items_html}</td>'
        rows_html += f'<tr class="lch-tr">{cells}</tr>'

    table_html = f"""
    <style>
      .lch-tbl .lch-tr:hover td {{ background: #f5f5f7 !important; }}
      .lch-tbl .lch-tr:last-child td {{ border-bottom: none !important; }}
    </style>
    <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                overflow:hidden;border:1px solid #e8e8ed;margin-bottom:8px">
      <div style="padding:16px 20px;border-bottom:1px solid #f2f2f7">
        <span style="font-size:14px;font-weight:600;color:#1d1d1f;font-family:{_AP_FONT}">
          近期开测信息 — {active_date}
        </span>
      </div>
      <div style="overflow:auto;max-height:700px">
        <table class="lch-tbl" style="border-collapse:collapse;font-size:14px;
               table-layout:fixed;font-family:{_AP_FONT};width:auto">
          <thead style="position:sticky;top:0;z-index:1">
            <tr>{header}</tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
      <div style="border-top:1px solid #f2f2f7;padding:10px 20px;font-size:12px;
                  color:#aeaeb2;font-family:{_AP_FONT};display:flex;gap:12px;flex-wrap:wrap">
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

    st.multiselect(
        "展示渠道",
        options=_all_launch_labels,
        default=_all_launch_labels,
        key=_lch_key,
    )


@st.cache_data(ttl=300)
def _cached_platforms_for_game(_db, game_name):
    return _db.get_platforms_for_game(game_name)


@st.cache_data(ttl=60)
def _cached_competitors(_db):
    return _db.get_competitors()


@st.cache_data(ttl=60)
def _cached_anomalies(_db, days=30):
    return _db.get_anomalies(days=days)


def render_competitor_monitor(db: Database):
    st.title("竞品监控")

    # ── 竞品管理 ──────────────────────────────────────────────────────────────
    st.subheader("竞品游戏管理")
    col_add1, col_add2 = st.columns([3, 1])
    with col_add1:
        new_game = st.text_input(
            "", placeholder="输入游戏名称（需与排行榜中显示名一致）",
            key="comp_add_name", label_visibility="collapsed",
        )
    with col_add2:
        if st.button("添加监控", key="comp_add_btn"):
            if new_game.strip():
                db.add_competitor(new_game.strip())
                _cached_competitors.clear()
                st.rerun()
            else:
                st.warning("请输入游戏名称")

    competitors = _cached_competitors(db)
    if competitors:
        for comp in competitors:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:14px;color:#1d1d1f;font-family:{_AP_FONT}">'
                    f'<b>{comp["game_name"]}</b>'
                    + (f' <span style="color:#6e6e73;font-size:12px">— {comp["notes"]}</span>'
                       if comp.get("notes") else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("删除", key=f"comp_del_{comp['game_name']}"):
                    db.remove_competitor(comp["game_name"])
                    _cached_competitors.clear()
                    st.rerun()
    else:
        st.info("尚未添加监控游戏，请在上方输入游戏名后点击「添加监控」。")

    st.divider()

    # ── 异动播报 ──────────────────────────────────────────────────────────────
    st.subheader("异动播报（近 30 天）")

    anomalies = _cached_anomalies(db, days=30)
    if not anomalies:
        st.info("暂无异动记录。每日运行 `python main.py competitor` 后，检测到异动会自动出现在此处。")
    else:
        for rec in anomalies:
            game_name    = rec["game_name"]
            fetch_date   = rec["fetch_date"]
            rank_changes = rec.get("rank_changes") or {}
            details      = rec.get("platform_details") or {}
            analysis     = rec.get("ai_analysis") or ""
            plts_changed = rec.get("platforms_changed") or []

            # 构建平台变化行
            chg_parts = []
            for plt, chg in rank_changes.items():
                t, y = chg.get("today"), chg.get("yesterday")
                if t is None:
                    chg_parts.append(f"{plt}: 跌出榜")
                elif y is None:
                    chg_parts.append(f"{plt}: 新进榜 #{t}")
                else:
                    arrow = "↑" if y > t else "↓"
                    chg_parts.append(f"{plt}: #{y}→#{t} {arrow}{abs(y - t)}")

            # 评分行
            rating_parts = []
            for plt, d in details.items():
                if d.get("rating"):
                    rating_parts.append(f"{plt} ⭐{d['rating']}")

            # 版本/更新内容
            whatsnew_parts = []
            for plt, d in details.items():
                if d.get("whatsnew"):
                    ver = f"v{d['version']} " if d.get("version") else ""
                    whatsnew_parts.append(f"**{plt}** {ver}— {d['whatsnew'][:150]}")

            card_html = f"""
            <div style="background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(0,0,0,.08);
                        overflow:hidden;border:1px solid #e8e8ed;margin-bottom:16px;
                        padding:20px 24px;font-family:{_AP_FONT}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
                <div>
                  <span style="font-size:17px;font-weight:700;color:#1d1d1f">{game_name}</span>
                  <span style="font-size:12px;color:#6e6e73;margin-left:10px">{fetch_date}</span>
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  {"".join(f'<span style="background:#f5f5f7;border:1px solid #d2d2d7;border-radius:20px;padding:3px 10px;font-size:12px;color:#1d1d1f">{p}</span>' for p in plts_changed)}
                </div>
              </div>
              <div style="font-size:13px;color:#1d1d1f;margin-bottom:8px;line-height:1.6">
                {"&nbsp;&nbsp;|&nbsp;&nbsp;".join(chg_parts)}
              </div>
              {('<div style="font-size:12px;color:#6e6e73;margin-bottom:8px">' + "&nbsp;&nbsp;".join(rating_parts) + "</div>") if rating_parts else ""}
              {('<div style="font-size:12px;color:#6e6e73;border-top:1px solid #f2f2f7;padding-top:8px;margin-bottom:8px;line-height:1.6">' + "<br>".join(p.replace("**","<b>",1).replace("**","</b>",1) for p in whatsnew_parts) + "</div>") if whatsnew_parts else ""}
              {"" if not analysis else f'<div style="font-size:13px;color:#1d1d1f;background:#f9f9fb;border-radius:10px;padding:12px 14px;line-height:1.7">{analysis}</div>'}
            </div>
            """
            st.html(card_html)

    st.divider()

    # ── 排名趋势 ──────────────────────────────────────────────────────────────
    st.subheader("排名趋势")
    competitors_now = _cached_competitors(db)
    comp_names = [c["game_name"] for c in competitors_now]
    if not comp_names:
        st.info("请先添加监控游戏。")
        return

    tr_c1, tr_c2, tr_c3, tr_c4 = st.columns([3, 2, 2, 1])
    with tr_c1:
        sel_comp_game = st.selectbox("游戏", comp_names, key="comp_trend_game")
    with tr_c2:
        plts_for_game = _cached_platforms_for_game(db, sel_comp_game) if sel_comp_game else []
        sel_comp_plt = st.selectbox(
            "平台", plts_for_game,
            format_func=lambda k: PLATFORMS.get(k, k),
            key="comp_trend_plt",
        ) if plts_for_game else None
    with tr_c3:
        _rt_opts = {"下载榜": "download", "畅销榜": "revenue", "预约榜": "reservation", "活跃榜": "active"}
        sel_comp_rt_label = st.selectbox("榜单类型", list(_rt_opts.keys()), key="comp_trend_rt")
        sel_comp_rt = _rt_opts[sel_comp_rt_label]

    if sel_comp_game and sel_comp_plt:
        trend_rows = _cached_trend(db, sel_comp_game, sel_comp_plt, sel_comp_rt)
        if len(trend_rows) > 1:
            tdf = pd.DataFrame(trend_rows)
            tdf.columns = ["日期", "排名"]
            fig = px.line(
                tdf, x="日期", y="排名", markers=True,
                title=f"{sel_comp_game} · {PLATFORMS.get(sel_comp_plt, sel_comp_plt)} · {RANK_TYPES.get(sel_comp_rt, sel_comp_rt)}",
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(dtick=86400000, tickformat="%m/%d")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("需要多天数据才能显示趋势图。")
    else:
        st.info("请选择游戏和平台。")


# ── 主体 ────────────────────────────────────────────────────────────────────
if sel_page == "国内排行榜":
    render_data(sel_date, sel_platform, sel_rank_type)

elif sel_page == "国内开测表":
    render_launches(db, sel_date, sel_platform)

elif sel_page == "海外排行榜-移动":
    render_overseas(db, sel_date, sel_rank_type, section="mobile")

elif sel_page == "海外排行榜-PC":
    render_overseas(db, sel_date, sel_rank_type, section="pc")

else:
    render_competitor_monitor(db)
