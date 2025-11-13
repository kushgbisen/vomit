#!/usr/bin/env python3
"""
Vomit - AI-powered CLI Task Manager
Transform brain dumps into organized, actionable todos across timeframes.
"""

import typer
from typing import Optional

app = typer.Typer(
    name="vomit",
    help="AI-powered CLI task manager - raw thoughts → clean todos",
    no_args_is_help=True,
)

@app.command()
def show(
    timeframe: Optional[str] = typer.Option(None, "--today", help="Show today's tasks"),
    week: bool = typer.Option(False, "--week", help="Show weekly goals"),
    done: bool = typer.Option(False, "--done", help="Show completed tasks only"),
    pending: bool = typer.Option(False, "--pending", help="Show incomplete tasks only"),
):
    """Display tasks from timeframe files"""
    typer.echo("📋 Task display functionality coming soon...")
    if timeframe:
        typer.echo(f"Showing {timeframe} tasks")
    if week:
        typer.echo("Showing weekly goals")
    if done:
        typer.echo("Filtering: completed tasks")
    if pending:
        typer.echo("Filtering: incomplete tasks")

@app.command()
def timer(
    minutes: int = typer.Argument(..., help="Timer duration in minutes"),
    task: Optional[int] = typer.Option(None, "--task", help="Link timer to task number"),
):
    """Start a countdown timer"""
    typer.echo(f"⏰ Starting {minutes}-minute timer")
    if task:
        typer.echo(f"Linked to task #{task}")

@app.command()
def pomodoro(
    task: int = typer.Argument(..., help="Task number for Pomodoro session"),
):
    """Start full Pomodoro cycle (25min work + 5min break)"""
    typer.echo(f"🍅 Starting Pomodoro for task #{task}")

@app.command()
def complete(
    task: int = typer.Argument(..., help="Task number to mark complete"),
):
    """Mark task as completed"""
    typer.echo(f"✅ Marking task #{task} as complete")

@app.command()
def focus(
    task: int = typer.Argument(..., help="Task number to focus on"),
    off: bool = typer.Option(False, "--off", help="Turn off focus mode"),
):
    """Focus on single task, hide others"""
    if off:
        typer.echo("👁️ Focus mode disabled")
    else:
        typer.echo(f"🎯 Focus on task #{task} - hiding others")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for tasks"),
):
    """Search tasks across all timeframe files"""
    typer.echo(f"🔍 Searching for: '{query}'")

@app.command()
def count():
    """Quick task summary"""
    typer.echo("📊 Task count functionality coming soon...")

@app.command()
def new_day():
    """Archive today, create fresh list"""
    typer.echo("🌅 Creating new day...")

@app.command()
def carry_forward():
    """Move unfinished tasks to tomorrow"""
    typer.echo("📤 Carrying forward unfinished tasks...")

@app.command()
def stats():
    """Simple completion summary"""
    typer.echo("📈 Stats functionality coming soon...")

@app.command()
def backup():
    """Create timestamped backup"""
    typer.echo("💾 Creating backup...")

@app.command()
def archive():
    """Archive old completed tasks"""
    typer.echo("📦 Archiving completed tasks...")

@app.command()
def panic():
    """Show only today's top 3 tasks"""
    typer.echo("🚨 Panic mode - showing top 3 tasks")

@app.command()
def overdue():
    """Find forgotten tasks"""
    typer.echo("⏰ Finding overdue tasks...")

@app.command()
def status():
    """Show active timer and progress"""
    typer.echo("📱 No active timers")

if __name__ == "__main__":
    app()