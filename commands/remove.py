import typer
import re
from typing import Optional, List
from rich.console import Console
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations
from core.validator import TaskValidator

app = typer.Typer(help="Remove tasks from different timeframes")
console = Console()


def find_matching_tasks(task_file, pattern: str, exact_match: bool = False) -> List[Task]:
    """Find tasks matching the given pattern"""
    if exact_match:
        return [task for task in task_file.tasks if task.content == pattern]
    else:
        pattern_lower = pattern.lower()
        return [task for task in task_file.tasks if pattern_lower in task.content.lower()]


def remove_task_from_timeframe(pattern: str, timeframe: Timeframe, exact_match: bool = False, force: bool = False) -> int:
    """Remove tasks matching pattern from timeframe, returns number of tasks removed"""
    file_ops = FileOperations()
    task_file = file_ops.read_task_file(timeframe)
    
    matching_tasks = find_matching_tasks(task_file, pattern, exact_match)
    
    if not matching_tasks:
        console.print(f"[yellow]No tasks found matching '{pattern}' in {timeframe.value}[/yellow]")
        return 0
    
    # Show tasks to be removed
    if not force:
        console.print(f"[blue]Found {len(matching_tasks)} task(s) matching '{pattern}' in {timeframe.value}:[/blue]")
        for i, task in enumerate(matching_tasks, 1):
            status = "✓" if task.completed else "○"
            console.print(f"  {i}. {status} {task.content}")
        
        # Ask for confirmation
        if len(matching_tasks) > 1:
            response = typer.confirm(f"Remove all {len(matching_tasks)} tasks?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                return 0
        else:
            response = typer.confirm(f"Remove task: '{matching_tasks[0].content}'?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                return 0
    
    # Remove tasks
    removed_count = 0
    for task in matching_tasks:
        if task_file.remove_task(task.content):
            removed_count += 1
    
    # Write back to file
    file_ops.write_task_file(task_file)
    
    return removed_count


@app.command()
def remove(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation")
):
    """Remove tasks matching a pattern"""
    
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
        # Default to today if no timeframe specified
        target_timeframes = [Timeframe.TODAY]
    
    total_removed = 0
    
    for tf in target_timeframes:
        removed = remove_task_from_timeframe(pattern, tf, exact, force)
        total_removed += removed
    
    if total_removed > 0:
        console.print(f"[green]✓[/green] Removed {total_removed} task(s) matching '{pattern}'")
    else:
        console.print(f"[yellow]No tasks removed[/yellow]")


@app.command()
def clear(
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Clear all timeframes"),
    force: bool = typer.Option(False, "--force", "-f", help="Force clear without confirmation")
):
    """Clear all tasks from timeframe(s)"""
    
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
        # Default to today if no timeframe specified
        target_timeframes = [Timeframe.TODAY]
    
    total_cleared = 0
    
    for tf in target_timeframes:
        file_ops = FileOperations()
        task_file = file_ops.read_task_file(tf)
        
        if not task_file.tasks:
            console.print(f"[yellow]No tasks to clear in {tf.value}[/yellow]")
            continue
        
        # Show tasks to be cleared
        if not force:
            console.print(f"[blue]Found {len(task_file.tasks)} task(s) in {tf.value}:[/blue]")
            for task in task_file.tasks:
                status = "✓" if task.completed else "○"
                console.print(f"  {status} {task.content}")
            
            response = typer.confirm(f"Clear all tasks from {tf.value}?")
            if not response:
                console.print(f"[yellow]Skipped {tf.value}[/yellow]")
                continue
        
        # Clear tasks
        task_file.tasks.clear()
        file_ops.write_task_file(task_file)
        total_cleared += len(task_file.tasks)
        
        timeframe_name = tf.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
        console.print(f"[green]✓[/green] Cleared {timeframe_name}")
    
    if total_cleared > 0:
        console.print(f"[green]✓[/green] Cleared {total_cleared} total task(s)")


if __name__ == "__main__":
    app()