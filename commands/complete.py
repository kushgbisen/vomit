import typer
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations
from core.validator import TaskValidator

app = typer.Typer(help="Complete tasks in different timeframes")
console = Console()


def find_matching_tasks(task_file, pattern: str, exact_match: bool = False) -> List[Task]:
    """Find tasks matching the given pattern"""
    if exact_match:
        return [task for task in task_file.tasks if task.content == pattern]
    else:
        pattern_lower = pattern.lower()
        return [task for task in task_file.tasks if pattern_lower in task.content.lower()]


def toggle_task_completion(task: Task) -> bool:
    """Toggle task completion status and update timestamps"""
    if task.completed:
        # Uncomplete the task
        task.completed = False
        task.completed_at = None
        return False  # Task is now incomplete
    else:
        # Complete the task
        task.completed = True
        task.completed_at = datetime.now()
        return True  # Task is now complete


def complete_task_in_timeframe(pattern: str, timeframe: Timeframe, exact_match: bool = False, force: bool = False, uncomplete: bool = False) -> int:
    """Complete/uncomplete tasks matching pattern in timeframe, returns number of tasks modified"""
    file_ops = FileOperations()
    task_file = file_ops.read_task_file(timeframe)
    
    matching_tasks = find_matching_tasks(task_file, pattern, exact_match)
    
    if not matching_tasks:
        console.print(f"[yellow]No tasks found matching '{pattern}' in {timeframe.value}[/yellow]")
        return 0
    
    # Filter tasks based on current completion status
    if uncomplete:
        matching_tasks = [task for task in matching_tasks if task.completed]
        action = "uncomplete"
    else:
        matching_tasks = [task for task in matching_tasks if not task.completed]
        action = "complete"
    
    if not matching_tasks:
        console.print(f"[yellow]No tasks to {action} matching '{pattern}' in {timeframe.value}[/yellow]")
        return 0
    
    # Show tasks to be modified
    if not force:
        console.print(f"[blue]Found {len(matching_tasks)} task(s) to {action} matching '{pattern}' in {timeframe.value}:[/blue]")
        for i, task in enumerate(matching_tasks, 1):
            status = "✓" if task.completed else "○"
            console.print(f"  {i}. {status} {task.content}")
        
        # Ask for confirmation
        if len(matching_tasks) > 1:
            response = typer.confirm(f"{action.capitalize()} all {len(matching_tasks)} tasks?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                return 0
        else:
            response = typer.confirm(f"{action.capitalize()} task: '{matching_tasks[0].content}'?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                return 0
    
    # Toggle task completion
    modified_count = 0
    for task in matching_tasks:
        was_completed = toggle_task_completion(task)
        if uncomplete:
            if not was_completed:  # Task was completed, now uncompleted
                modified_count += 1
        else:
            if was_completed:  # Task was incomplete, now completed
                modified_count += 1
    
    # Write back to file
    file_ops.write_task_file(task_file)
    
    return modified_count


@app.command()
def complete(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    force: bool = typer.Option(False, "--force", "-f", help="Force completion without confirmation")
):
    """Complete tasks matching a pattern"""
    
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
    
    total_completed = 0
    
    for tf in target_timeframes:
        completed = complete_task_in_timeframe(pattern, tf, exact, force, uncomplete=False)
        total_completed += completed
    
    if total_completed > 0:
        console.print(f"[green]✓[/green] Completed {total_completed} task(s) matching '{pattern}'")
    else:
        console.print(f"[yellow]No tasks completed[/yellow]")


@app.command()
def uncomplete(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    force: bool = typer.Option(False, "--force", "-f", help="Force uncompletion without confirmation")
):
    """Uncomplete tasks matching a pattern"""
    
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
    
    total_uncompleted = 0
    
    for tf in target_timeframes:
        uncompleted = complete_task_in_timeframe(pattern, tf, exact, force, uncomplete=True)
        total_uncompleted += uncompleted
    
    if total_uncompleted > 0:
        console.print(f"[green]✓[/green] Uncompleted {total_uncompleted} task(s) matching '{pattern}'")
    else:
        console.print(f"[yellow]No tasks uncompleted[/yellow]")


@app.command()
def toggle(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    force: bool = typer.Option(False, "--force", "-f", help="Force toggle without confirmation")
):
    """Toggle completion status of tasks matching a pattern"""
    
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
    
    total_toggled = 0
    
    for tf in target_timeframes:
        file_ops = FileOperations()
        task_file = file_ops.read_task_file(tf)
        
        matching_tasks = find_matching_tasks(task_file, pattern, exact)
        
        if not matching_tasks:
            console.print(f"[yellow]No tasks found matching '{pattern}' in {tf.value}[/yellow]")
            continue
        
        # Show tasks to be toggled
        if not force:
            console.print(f"[blue]Found {len(matching_tasks)} task(s) to toggle matching '{pattern}' in {tf.value}:[/blue]")
            for i, task in enumerate(matching_tasks, 1):
                status = "✓" if task.completed else "○"
                console.print(f"  {i}. {status} {task.content}")
            
            # Ask for confirmation
            if len(matching_tasks) > 1:
                response = typer.confirm(f"Toggle all {len(matching_tasks)} tasks?")
                if not response:
                    console.print(f"[yellow]Skipped {tf.value}[/yellow]")
                    continue
            else:
                response = typer.confirm(f"Toggle task: '{matching_tasks[0].content}'?")
                if not response:
                    console.print(f"[yellow]Skipped {tf.value}[/yellow]")
                    continue
        
        # Toggle tasks
        for task in matching_tasks:
            toggle_task_completion(task)
        
        # Write back to file
        file_ops.write_task_file(task_file)
        total_toggled += len(matching_tasks)
    
    if total_toggled > 0:
        console.print(f"[green]✓[/green] Toggled {total_toggled} task(s) matching '{pattern}'")
    else:
        console.print(f"[yellow]No tasks toggled[/yellow]")


if __name__ == "__main__":
    app()