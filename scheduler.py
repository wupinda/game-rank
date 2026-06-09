"""
每日定时调度器
默认每天 09:00 自动执行：抓取所有平台排行榜 → 保存到数据库 → 导出 Excel
"""
import logging
import time
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console

console = Console()
logger  = logging.getLogger(__name__)


def job(cfg: dict):
    """定时任务执行体"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"\n[bold cyan]═══ 定时任务开始 {ts} ═══[/bold cyan]")

    # 1. 抓取
    from main import run_fetch, do_export
    items = run_fetch(cfg)
    console.print(f"[green]抓取完成，共 {len(items)} 条[/green]")

    # 2. 导出 Excel
    if cfg.get("schedule", {}).get("export_excel", True) and items:
        path = do_export(cfg, items)
        if path:
            console.print(f"[green]Excel 已保存: {path}[/green]")

    console.print(f"[bold cyan]═══ 定时任务完成 ═══[/bold cyan]\n")


def start(cfg: dict):
    sched_cfg  = cfg.get("schedule", {})
    run_time   = sched_cfg.get("time", "09:00")
    hour, minute = run_time.split(":")

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    trigger   = CronTrigger(hour=int(hour), minute=int(minute), timezone="Asia/Shanghai")
    scheduler.add_job(job, trigger, args=[cfg], id="daily_rank")

    next_run = scheduler.get_jobs()[0].next_run_time
    console.print(f"[bold green]定时任务已启动，每天 {run_time} 执行[/bold green]")
    console.print(f"[dim]下次执行: {next_run}[/dim]")
    console.print("[dim]按 Ctrl+C 停止[/dim]\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("\n[yellow]定时任务已停止[/yellow]")
