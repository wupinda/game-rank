# 游戏渠道排行榜工具

多渠道游戏排行榜自动抓取与可视化看板。每日定时采集各大应用商店/游戏平台的排行榜数据和近期开测信息，通过 Streamlit 看板展示。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 排行榜抓取 | 7 个平台，覆盖下载榜、畅销榜、活跃榜、预约榜 |
| 开测表 | B站、TapTap、好游快爆三渠道近期开测/公测信息 |
| 排名变化 | 对比前一日排名，显示上升/下降/新上榜 |
| 排名趋势图 | 指定游戏在特定平台的历史排名折线图 |
| 每日定时任务 | Windows Task Scheduler 每天 09:00 自动抓取 |
| Excel 导出 | 一键导出当日数据到 Excel |

---

## 目录结构

```
game_rank_tool/
├── main.py               # CLI 入口（fetch / dashboard / export / test）
├── dashboard.py          # Streamlit 看板
├── config.yaml           # 配置文件（代理、定时、平台开关等）
├── scheduler.py          # APScheduler 定时任务封装
├── scrapers/
│   ├── base.py           # 基类、数据类（RankItem / LaunchItem）
│   ├── appstore.py       # App Store
│   ├── taptap.py         # TapTap
│   ├── bilibili.py       # B站游戏
│   ├── xiaomi.py         # 小米游戏
│   ├── kuaibao.py        # 好游快爆排行榜
│   ├── wegame.py         # WeGame（端游）
│   ├── myapp.py          # 应用宝
│   ├── bilibili_launch.py   # B站 开测表爬虫
│   ├── taptap_calendar.py   # TapTap 近期焦点（开测表爬虫）
│   └── kuaibao_timeline.py  # 好游快爆 即将上线（开测表爬虫）
├── storage/
│   └── db.py             # SQLite 封装（rankings + launches 两张表）
├── utils/
│   └── export.py         # Excel 导出工具
└── data/
    ├── rankings.db       # SQLite 数据库（自动生成，勿删）
    └── *.xlsx            # 导出的 Excel 文件
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：`requests`、`beautifulsoup4`、`streamlit`、`plotly`、`openpyxl`、`click`、`pyyaml`、`rich`、`apscheduler`

### 2. 抓取数据

```bash
python main.py fetch
```

抓取所有平台排行榜 + 开测表数据，保存到 `data/rankings.db`。首次运行约需 1～2 分钟。

### 3. 启动看板

```bash
python main.py dashboard
# 或
streamlit run dashboard.py
```

浏览器访问 `http://localhost:8501`

---

## 常用命令

```bash
# 抓取所有平台（排行榜 + 开测表）
python main.py fetch

# 只抓取指定平台排行榜
python main.py fetch --platform taptap

# 抓取后自动导出 Excel
python main.py fetch --export

# 只抓排行榜，跳过开测表
python main.py fetch --no-launches

# 导出最新数据到 Excel
python main.py export

# 连通性测试（每个平台抓 Top3，快速验证）
python main.py test

# 启动看板
python main.py dashboard
```

---

## 排行榜渠道说明

| 平台 key | 显示名 | 支持榜单 | 数据来源方式 |
|----------|--------|----------|-------------|
| `appstore` | App Store | 下载榜、畅销榜 | Apple RSS JSON API |
| `taptap` | TapTap | 热门榜、预约榜 | taptap.cn Web API |
| `bilibili` | B站 | 预约榜 | le3-api.game.bilibili.com |
| `xiaomi` | 小米 | 下载榜、活跃榜 | game.xiaomi.com API |
| `kuaibao` | 快爆 | 下载榜 | 好游快爆 Web API |
| `wegame` | WeGame | 新品榜、热门榜 | wegame.com.cn API |
| `myapp` | 应用宝 | 下载榜、畅销榜 | 应用宝 Web API |

在 `config.yaml` 中可以按 key 单独禁用某个平台：

```yaml
platforms:
  appstore: true
  wegame: false   # 禁用该平台
```

---

## 开测表渠道说明

开测表与排行榜独立，显示近期即将开测/公测的游戏。

| 渠道 | 数据来源 | 说明 |
|------|----------|------|
| B站 | `le3-api.game.bilibili.com/pc/game/ranking/page_start_test_list` | 开测列表，含具体开测时间 |
| TapTap | `taptap.cn/webapiv2/calendar/v1/event-list` | 近期焦点（event_level=1），抓取未来 60 天 |
| 好游快爆 | `3839.com/timeline.html` HTML 解析 | 即将上线 tab（panelList rel=1） |

开测类型颜色规则：绿色=首发/公测/不删档，蓝色=预约，橙色=删档测试，灰色=其他。

好游快爆过滤规则：只保留有明确开测类型的游戏，剔除直播、海外试玩、上线试玩等不相关节点。

---

## 看板功能说明

### 排行榜 Tab

- **左侧筛选**：日期、平台（全部/单选）、榜单类型（默认预约榜）
- **指标卡**：平台数、榜单类型数、总记录数、去重游戏数
- **Top 20 对比表**：多平台横向对比，每日排名变化（▲▼/NEW/-）
- **Excel 导出**：按当前筛选条件导出
- **排名趋势图**：选择游戏后显示历史折线（需选择具体平台+榜单）
- **自动刷新**：左侧可开启，支持 1/5/10/30 分钟间隔

### 开测表 Tab

- 以时间为行、渠道为列的透视表
- 只显示今天及之后的日期，"待定"（无具体日期）排在末尾
- 每格显示该渠道在该日期的所有游戏及开测类型

---

## 定时任务（Windows Task Scheduler）

已配置每天 09:00 自动执行 `python main.py fetch`，日志写入 `data/game_rank.log`。

查看或修改任务：任务计划程序 → 任务计划程序库 → `GameRankFetch`

---

## 数据存储说明

数据保存在 `data/rankings.db`（SQLite），包含两张表：

- **`rankings`**：排行榜数据，按 `(platform, rank_type, fetch_date)` 索引
- **`launches`**：开测表数据，按 `(platform, fetch_date)` 索引

每次抓取先删除当日旧数据（幂等），再写入新数据，保证每日只保留一份。

---

## 技术栈

- **爬虫**：`requests` + `BeautifulSoup4`，纯 HTTP 请求，无需浏览器
- **存储**：SQLite（`sqlite3` 标准库）
- **看板**：Streamlit + Plotly
- **CLI**：Click + Rich
- **定时**：Windows Task Scheduler（主）/ APScheduler（备）
