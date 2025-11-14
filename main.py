#!/usr/bin/env python3
"""
Vomit - AI-powered CLI Task Manager
Transform brain dumps into organized, actionable todos across timeframes.
"""

import typer
import sys
from pathlib import Path
from typing import Optional

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import command functions directly
from commands.add import add, quick
from commands.remove import remove, clear
from commands.complete import complete, uncomplete, toggle
from commands.search import search, find, completed, incomplete
from commands.status import status, progress, overview
from commands.move import move, promote, demote, cleanup

app = typer.Typer(
    name="vomit",
    help="AI-powered CLI task manager - raw thoughts → clean todos",
    no_args_is_help=True,
)

# Register add commands
app.command()(add)
app.command()(quick)

# Register remove commands
app.command()(remove)
app.command()(clear)

# Register complete commands
app.command()(complete)
app.command()(uncomplete)
app.command()(toggle)

# Register search commands
app.command()(search)
app.command()(find)
app.command()(completed)
app.command()(incomplete)

# Register status commands
app.command()(status)
app.command()(progress)
app.command()(overview)

# Register move commands
app.command()(move)
app.command()(promote)
app.command()(demote)
app.command()(cleanup)

# Legacy commands for backward compatibility
@app.command()
def show(
    timeframe: Optional[str] = typer.Option(None, "--today", help="Show today's tasks"),
    week: bool = typer.Option(False, "--week", help="Show weekly goals"),
    done: bool = typer.Option(False, "--done", help="Show completed tasks only"),
    pending: bool = typer.Option(False, "--pending", help="Show incomplete tasks only"),
):
    """Display tasks from timeframe files"""
    typer.echo("Use 'vomit status' for task display functionality")
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
def complete_legacy(
    task: int = typer.Argument(..., help="Task number to mark complete"),
):
    """Mark task as completed (legacy - use 'vomit complete' instead)"""
    typer.echo("Use 'vomit complete \"task name\"' instead")
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
def search_legacy(
    query: str = typer.Argument(..., help="Search query for tasks"),
):
    """Search tasks across all timeframe files (legacy - use 'vomit search' instead)"""
    typer.echo("Use 'vomit search \"query\"' instead")
    typer.echo(f"🔍 Searching for: '{query}'")

@app.command()
def count():
    """Quick task summary"""
    typer.echo("📊 Use 'vomit status overview' for task count")

@app.command()
def new_day():
    """Archive today, create fresh list"""
    typer.echo("🌅 Creating new day...")
    typer.echo("Use 'vomit cleanup --timeframe today' to archive completed tasks")

@app.command()
def carry_forward():
    """Move unfinished tasks to tomorrow"""
    typer.echo("📤 Carrying forward unfinished tasks...")
    typer.echo("Use 'vomit move \"pattern\" --from today --to week' to move tasks")

@app.command()
def stats():
    """Simple completion summary"""
    typer.echo("📈 Use 'vomit status --summary' for stats")

@app.command()
def backup():
    """Create timestamped backup"""
    typer.echo("💾 Creating backup...")
    typer.echo("Backup functionality coming soon...")

@app.command()
def archive():
    """Archive old completed tasks"""
    typer.echo("📦 Use 'vomit cleanup' to archive completed tasks")

@app.command()
def panic():
    """Show only today's top 3 tasks"""
    typer.echo("🚨 Panic mode - showing top 3 tasks")
    typer.echo("Use 'vomit search \"\" --timeframe today --force' to see all tasks")

@app.command()
def overdue():
    """Find forgotten tasks"""
    typer.echo("⏰ Finding overdue tasks...")
    typer.echo("Use 'vomit status --details' to find old tasks")

@app.command()
def status_legacy():
    """Show active timer and progress"""
    typer.echo("📱 No active timers")
    typer.echo("Use 'vomit status' for task status")

if __name__ == "__main__":
    app()