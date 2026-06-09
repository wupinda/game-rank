#!/usr/bin/env python3
"""
游戏排行榜抓取工具 - 命令行入口
用法：
  python main.py fetch                   # 抓取所有平台
  python main.py fetch --platform taptap # 抓取单一平台
  python main.py export                  # 导出最新数据到 Excel
  python main.py schedule                # 启动每日定时任务
  python main.py dashboard               # 启动 Streamlit 可视化面板
  python main.py test                    # 测试各平台爬虫连通性
"""
import os
import sys
import logging
from datetime import date

import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console(highlight=False)


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(cfg: dict):
    level = getattr(logging, cfg.get("logging", {}).get("level", "INFO"), logging.INFO)
    log_file = cfg.get("logging", {}).get("file", "./data/game_rank.log")
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def get_proxies(cfg: dict) -> dict:
    proxy_cfg = cfg.get("proxy", {})
    if proxy_cfg.get("enabled"):
        return {"http": proxy_cfg.get("http"), "https": proxy_cfg.get("https")}
    return None


def run_fetch(cfg: dict, platform_filter: str = None) -> list:
    from scrapers import ALL_SCRAPERS
    from scrapers.base import PLATFORMS
    from storage import Database

    db      = Database(url=cfg["supabase"]["url"], key=cfg["supabase"]["key"])
    proxies = get_proxies(cfg)
    top_n   = cfg["general"].get("top_n", 20)
    enabled = cfg.get("platforms", {})

    all_items = []
    for key, scraper_cls in ALL_SCRAPERS.items():
        if platform_filter and key != platform_filter:
            continue
        if not enabled.get(key, True):
            continue
        scraper = scraper_cls(proxies=proxies)
        scraper.TOP_N = top_n
        items = scraper.fetch_all()
        all_items.extend(items)

    if all_items:
        today = date.today().isoformat()
        fetched_platforms = {it.platform for it in all_items}
        for plt in fetched_platforms:
            db.delete_by_date(today, platform=plt)
        db.save(all_items)
        console.print(f"[green]OK 保存 {len(all_items)} 条记录到数据库[/green]")
    return all_items


def run_fetch_launches(cfg: dict) -> list:
    from scrapers import ALL_LAUNCH_SCRAPERS
    from scrapers.base import PLATFORMS
    from storage import Database

    db      = Database(url=cfg["supabase"]["url"], key=cfg["supabase"]["key"])
    proxies = get_proxies(cfg)
    enabled = cfg.get("platforms", {})
    today   = date.today().isoformat()

    all_items = []
    for key, scraper_cls in ALL_LAUNCH_SCRAPERS.items():
        if not enabled.get(key, True):
            continue
        scraper = scraper_cls(proxies=proxies)
        try:
            items = scraper.fetch_launches()
            all_items.extend(items)
            label = PLATFORMS.get(key, key)
            console.print(f"  [cyan]{label}[/cyan] 开测数据 {len(items)} 条")
        except Exception as exc:
            console.print(f"  [red]FAIL[/red] {PLATFORMS.get(key, key)}: {exc}")

    if all_items:
        db.delete_launches_by_date(today)
        db.save_launches(all_items)
        console.print(f"[green]OK 保存 {len(all_items)} 条开测数据到数据库[/green]")
    return all_items


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    cfg = load_config()
    setup_logging(cfg)
    ctx.obj["cfg"] = cfg


@cli.command()
@click.option("--platform", "-p", default=None, help="指定平台 (appstore/taptap/bilibili/...)")
@click.option("--export", "-e", is_flag=True, default=False, help="抓取后自动导出 Excel")
@click.option("--no-launches", is_flag=True, default=False, help="跳过开测表数据抓取")
@click.pass_context
def fetch(ctx, platform, export, no_launches):
    """立即抓取所有（或指定）平台的排行榜及开测数据"""
    cfg   = ctx.obj["cfg"]
    items = run_fetch(cfg, platform)

    if not platform and not no_launches:
        console.print("\n[bold]抓取开测数据…[/bold]")
        run_fetch_launches(cfg)

    if not items:
        console.print("[yellow]未获取到任何数据[/yellow]")
        return

    # 打印结果摘要
    from scrapers.base import PLATFORMS, RANK_TYPES
    tbl = Table(title="抓取摘要", show_lines=True)
    tbl.add_column("平台",   style="cyan")
    tbl.add_column("榜单",   style="magenta")
    tbl.add_column("数量",   justify="right")
    tbl.add_column("TOP1",  style="green")

    from itertools import groupby
    key_fn = lambda x: (x.platform, x.rank_type)
    for (platform_key, rank_type), grp in groupby(sorted(items, key=key_fn), key=key_fn):
        grp_list = list(grp)
        top1     = grp_list[0].name if grp_list else "—"
        tbl.add_row(
            PLATFORMS.get(platform_key, platform_key),
            RANK_TYPES.get(rank_type, rank_type),
            str(len(grp_list)),
            top1,
        )
    console.print(tbl)

    if export or cfg.get("schedule", {}).get("export_excel"):
        do_export(cfg, items)


def do_export(cfg: dict, items=None):
    from utils import Exporter
    from storage import Database

    output_dir = cfg["general"].get("output_dir", "./data")
    exp        = Exporter(output_dir)

    if items is None:
        db    = Database(url=cfg["supabase"]["url"], key=cfg["supabase"]["key"])
        dates = db.available_dates()
        if not dates:
            console.print("[yellow]数据库暂无数据[/yellow]")
            return
        rows  = db.query(fetch_date=dates[0])
        from scrapers.base import RankItem
        items = [
            RankItem(
                rank=r["rank_pos"], name=r["game_name"],
                platform=r["platform"], rank_type=r["rank_type"],
                game_id=r["game_id"], developer=r["developer"],
                icon_url=r["icon_url"], rating=r["rating"],
                fetch_date=r["fetch_date"],
            )
            for r in rows
        ]

    if not items:
        console.print("[yellow]无数据可导出[/yellow]")
        return

    fetch_date = items[0].fetch_date
    path       = exp.to_excel(items, fetch_date)
    console.print(f"[green]OK Excel 已导出: {path}[/green]")
    return path


@cli.command()
@click.option("--date", "-d", "fetch_date", default=None, help="指定日期 YYYY-MM-DD（默认最新）")
@click.option("--format", "-f", "fmt", default="excel", type=click.Choice(["excel"]))
@click.pass_context
def export(ctx, fetch_date, fmt):
    """导出数据到 Excel"""
    cfg = ctx.obj["cfg"]
    do_export(cfg)


@cli.command()
@click.pass_context
def schedule(ctx):
    """启动每日定时任务（默认每天 09:00 抓取）"""
    import scheduler as sched_module
    cfg = ctx.obj["cfg"]
    sched_module.start(cfg)


@cli.command()
@click.pass_context
def dashboard(ctx):
    """启动 Streamlit 可视化面板"""
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "dashboard.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


@cli.command()
@click.pass_context
def test(ctx):
    """测试各平台爬虫连通性（每个平台仅抓一个榜单 Top3）"""
    from scrapers import ALL_SCRAPERS
    from scrapers.base import PLATFORMS, RANK_TYPES

    cfg     = ctx.obj["cfg"]
    proxies = get_proxies(cfg)

    tbl = Table(title="连通性测试", show_lines=True)
    tbl.add_column("平台",   style="cyan", width=12)
    tbl.add_column("榜单",   style="magenta", width=8)
    tbl.add_column("状态",   width=6)
    tbl.add_column("TOP1",  style="green")

    for key, scraper_cls in ALL_SCRAPERS.items():
        if not ctx.obj["cfg"].get("platforms", {}).get(key, True):
            continue
        scraper = scraper_cls(proxies=proxies)
        scraper.TOP_N = 3
        rank_type = scraper.SUPPORTED_RANK_TYPES[0] if scraper.SUPPORTED_RANK_TYPES else "download"
        try:
            items = scraper.fetch(rank_type)
            status = "[green]OK[/green]"
            top1   = items[0].name if items else "(空)"
        except Exception as e:
            status = "[red]FAIL[/red]"
            top1   = str(e)[:60]
        tbl.add_row(
            PLATFORMS.get(key, key),
            RANK_TYPES.get(rank_type, rank_type),
            status,
            top1,
        )

    console.print(tbl)


if __name__ == "__main__":
    cli()
