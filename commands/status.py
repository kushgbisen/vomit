import typer
from typing import Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations

app = typer.Typer(help="Show task status and progress")
console = Console()


def calculate_progress(task_file) -> tuple[int, int, float]:
    """Calculate progress for a task file
    Returns (completed_count, total_count, percentage)
    """
    completed = task_file.get_completed_count()
    total = task_file.get_total_count()
    percentage = (completed / total * 100) if total > 0 else 0.0
    return completed, total, percentage


def format_progress_bar(percentage: float, width: int = 20) -> str:
    """Create a simple text progress bar"""
    filled = int(percentage / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage:.1f}%"


def get_recently_completed(task_file, days: int = 7) -> list[Task]:
    """Get tasks completed in the last N days"""
    cutoff_date = datetime.now() - timedelta(days=days)
    recently_completed = []
    
    for task in task_file.tasks:
        if task.completed and task.completed_at and task.completed_at >= cutoff_date:
            recently_completed.append(task)
    
    return sorted(recently_completed, key=lambda t: t.completed_at, reverse=True)


def get_overdue_tasks(task_file) -> list[Task]:
    """Get incomplete tasks that might be overdue (simplified)"""
    # This is a simple implementation - could be enhanced with due dates
    # For now, just return incomplete tasks from older timeframes
    return [task for task in task_file.tasks if not task.completed]


def show_timeframe_status(timeframe: Timeframe, show_details: bool = False):
    """Show status for a specific timeframe"""
    file_ops = FileOperations()
    task_file = file_ops.read_task_file(timeframe)
    
    completed, total, percentage = calculate_progress(task_file)
    
    # Format timeframe name
    timeframe_name = timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
    
    # Create progress bar
    progress_text = format_progress_bar(percentage)
    
    # Main status line
    status_text = f"[bold]{timeframe_name}[/bold]: {completed}/{total} complete ({progress_text})"
    
    if total == 0:
        console.print(f"[bold]{timeframe_name}[/bold]: [dim]No tasks[/dim]")
        return
    
    console.print(status_text)
    
    # Show details if requested
    if show_details and total > 0:
        # Recently completed
        recently_completed = get_recently_completed(task_file)
        if recently_completed:
            console.print("\n[green]Recently completed (last 7 days):[/green]")
            for task in recently_completed[:5]:  # Show max 5
                days_ago = (datetime.now() - task.completed_at).days
                console.print(f"  ✓ {task.content} [dim]({days_ago} days ago)[/dim]")
        
        # Incomplete tasks
        incomplete_tasks = [task for task in task_file.tasks if not task.completed]
        if incomplete_tasks:
            console.print(f"\n[yellow]Incomplete ({len(incomplete_tasks)}):[/yellow]")
            for task in incomplete_tasks[:10]:  # Show max 10
                console.print(f"  ○ {task.content}")


def show_overall_summary():
    """Show overall summary across all timeframes"""
    file_ops = FileOperations()
    
    total_completed = 0
    total_tasks = 0
    timeframe_stats = {}
    
    # Collect stats from all timeframes
    for timeframe in Timeframe:
        task_file = file_ops.read_task_file(timeframe)
        completed, total, percentage = calculate_progress(task_file)
        
        total_completed += completed
        total_tasks += total
        
        timeframe_name = timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
        timeframe_stats[timeframe_name] = {
            'completed': completed,
            'total': total,
            'percentage': percentage
        }
    
    # Overall progress
    overall_percentage = (total_completed / total_tasks * 100) if total_tasks > 0 else 0.0
    progress_text = format_progress_bar(overall_percentage, width=30)
    
    # Create summary panel
    summary_text = f"""
[bold]Overall Progress:[/bold] {total_completed}/{total_tasks} tasks complete
{progress_text}

[bold]Breakdown by timeframe:[/bold]
"""
    for name, stats in timeframe_stats.items():
        if stats['total'] > 0:
            summary_text += f"  {name}: {stats['completed']}/{stats['total']} ({stats['percentage']:.1f}%)\n"
    
    console.print(Panel(summary_text.strip(), title="📊 Task Summary", border_style="blue"))


@app.command()
def status(
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    details: bool = typer.Option(False, "--details", "-d", help="Show detailed information"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Show all timeframes"),
    summary: bool = typer.Option(False, "--summary", "-s", help="Show overall summary")
):
    """Show task status for timeframes"""
    
    # Map timeframe string to enum
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    if summary:
        show_overall_summary()
        return
    
    target_timeframes = []
    
    if all_timeframes:
        target_timeframes = list(Timeframe)
    elif timeframe:
        if timeframe.lower() not in timeframe_map:
            console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
            console.print("Available timeframes: today, week, month, year, vomit")
            raise typer.Exit(1)
        target_timeframes = [timeframe_map[timeframe.lower()]]
    else:
        # Default to today if no timeframe specified
        target_timeframes = [Timeframe.TODAY]
    
    # Show status for each timeframe
    for tf in target_timeframes:
        if len(target_timeframes) > 1:
            console.print()  # Add spacing between timeframes
        show_timeframe_status(tf, show_details=details)


@app.command()
def progress(
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Show progress for all timeframes")
):
    """Show visual progress bars"""
    
    # Map timeframe string to enum
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    target_timeframes = []
    
    if all_timeframes:
        target_timeframes = list(Timeframe)
    elif timeframe:
        if timeframe.lower() not in timeframe_map:
            console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
            console.print("Available timeframes: today, week, month, year, vomit")
            raise typer.Exit(1)
        target_timeframes = [timeframe_map[timeframe.lower()]]
    else:
        target_timeframes = list(Timeframe)  # Default to all for progress
    
    # Create progress table
    table = Table(title="📈 Task Progress", show_header=True, header_style="bold blue")
    table.add_column("Timeframe", style="cyan", width=15)
    table.add_column("Progress", style="green", width=40)
    table.add_column("Completed", style="yellow", width=12)
    table.add_column("Total", style="red", width=8)
    
    file_ops = FileOperations()
    
    for tf in target_timeframes:
        task_file = file_ops.read_task_file(tf)
        completed, total, percentage = calculate_progress(task_file)
        
        timeframe_name = tf.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
        
        # Create progress bar
        progress_bar = Progress(
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True
        )
        
        # Add row to table
        progress_text = format_progress_bar(percentage, width=30)
        table.add_row(
            timeframe_name,
            progress_text,
            str(completed),
            str(total)
        )
    
    console.print(table)


@app.command()
def overview():
    """Show quick overview of all timeframes"""
    file_ops = FileOperations()
    
    console.print("[bold]📋 Quick Overview[/bold]\n")
    
    for timeframe in Timeframe:
        task_file = file_ops.read_task_file(timeframe)
        completed, total, percentage = calculate_progress(task_file)
        
        timeframe_name = timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
        
        if total == 0:
            console.print(f"[dim]{timeframe_name}: Empty[/dim]")
        else:
            progress_text = format_progress_bar(percentage, width=15)
            console.print(f"{timeframe_name}: {progress_text} ({completed}/{total})")


if __name__ == "__main__":
    app()