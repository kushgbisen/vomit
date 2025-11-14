import typer
from typing import Optional, List
from rich.console import Console
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations
from core.validator import TaskValidator

app = typer.Typer(help="Move tasks between timeframes")
console = Console()


def find_matching_tasks(task_file, pattern: str, exact_match: bool = False) -> List[Task]:
    """Find tasks matching the given pattern"""
    if exact_match:
        return [task for task in task_file.tasks if task.content == pattern]
    else:
        pattern_lower = pattern.lower()
        return [task for task in task_file.tasks if pattern_lower in task.content.lower()]


def validate_timeframe_move(from_timeframe: Timeframe, to_timeframe: Timeframe) -> bool:
    """Validate that moving between timeframes makes sense"""
    if from_timeframe == to_timeframe:
        console.print(f"[red]Cannot move tasks from {from_timeframe.value} to the same timeframe[/red]")
        return False
    
    # Additional validation rules could be added here
    # For example, prevent moving from vomit to vomit, etc.
    
    return True


def move_task_to_timeframe(task: Task, from_timeframe: Timeframe, to_timeframe: Timeframe) -> bool:
    """Move a single task from one timeframe to another"""
    file_ops = FileOperations()
    
    # Read source file
    from_file = file_ops.read_task_file(from_timeframe)
    
    # Remove task from source
    if not from_file.remove_task(task.content):
        console.print(f"[red]Task not found in {from_timeframe.value}: {task.content}[/red]")
        return False
    
    # Read destination file
    to_file = file_ops.read_task_file(to_timeframe)
    
    # Add task to destination
    to_file.add_task(task)
    
    # Write both files
    file_ops.write_task_file(from_file)
    file_ops.write_task_file(to_file)
    
    return True


def format_timeframe_name(timeframe: Timeframe) -> str:
    """Format timeframe name for display"""
    return timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()


@app.command()
def move(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    from_timeframe: str = typer.Option(..., "--from", "-f", help="Source timeframe: today, week, month, year, vomit"),
    to_timeframe: str = typer.Option(..., "--to", "-t", help="Destination timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    force: bool = typer.Option(False, "--force", "-f", help="Force move without confirmation")
):
    """Move tasks from one timeframe to another"""
    
    # Map timeframe string to enum
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    # Validate source timeframe
    if from_timeframe.lower() not in timeframe_map:
        console.print(f"[red]Invalid source timeframe: {from_timeframe}[/red]")
        console.print("Available timeframes: today, week, month, year, vomit")
        raise typer.Exit(1)
    
    # Validate destination timeframe
    if to_timeframe.lower() not in timeframe_map:
        console.print(f"[red]Invalid destination timeframe: {to_timeframe}[/red]")
        console.print("Available timeframes: today, week, month, year, vomit")
        raise typer.Exit(1)
    
    from_tf = timeframe_map[from_timeframe.lower()]
    to_tf = timeframe_map[to_timeframe.lower()]
    
    # Validate move
    if not validate_timeframe_move(from_tf, to_tf):
        raise typer.Exit(1)
    
    # Find matching tasks
    file_ops = FileOperations()
    from_file = file_ops.read_task_file(from_tf)
    
    matching_tasks = find_matching_tasks(from_file, pattern, exact)
    
    if not matching_tasks:
        console.print(f"[yellow]No tasks found matching '{pattern}' in {from_tf.value}[/yellow]")
        raise typer.Exit(1)
    
    # Show tasks to be moved
    if not force:
        from_name = format_timeframe_name(from_tf)
        to_name = format_timeframe_name(to_tf)
        
        console.print(f"[blue]Found {len(matching_tasks)} task(s) to move from {from_name} to {to_name}:[/blue]")
        for i, task in enumerate(matching_tasks, 1):
            status = "✓" if task.completed else "○"
            console.print(f"  {i}. {status} {task.content}")
        
        # Ask for confirmation
        if len(matching_tasks) > 1:
            response = typer.confirm(f"Move all {len(matching_tasks)} tasks?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(1)
        else:
            response = typer.confirm(f"Move task: '{matching_tasks[0].content}'?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(1)
    
    # Move tasks
    moved_count = 0
    for task in matching_tasks:
        if move_task_to_timeframe(task, from_tf, to_tf):
            moved_count += 1
        else:
            console.print(f"[red]Failed to move task: {task.content}[/red]")
    
    # Show result
    from_name = format_timeframe_name(from_tf)
    to_name = format_timeframe_name(to_tf)
    
    if moved_count > 0:
        console.print(f"[green]✓[/green] Moved {moved_count} task(s) from {from_name} to {to_name}")
    else:
        console.print(f"[red]No tasks were moved[/red]")


@app.command()
def promote(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: str = typer.Option(..., "--timeframe", "-t", help="Current timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    force: bool = typer.Option(False, "--force", "-f", help="Force promotion without confirmation")
):
    """Promote tasks to a shorter timeframe (e.g., week → today)"""
    
    # Define promotion hierarchy (shorter to longer)
    promotion_hierarchy = [
        Timeframe.TODAY,
        Timeframe.WEEK,
        Timeframe.MONTH,
        Timeframe.YEAR,
        Timeframe.VOMIT
    ]
    
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    # Validate current timeframe
    if timeframe.lower() not in timeframe_map:
        console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
        console.print("Available timeframes: today, week, month, year, vomit")
        raise typer.Exit(1)
    
    current_tf = timeframe_map[timeframe.lower()]
    
    # Find current position in hierarchy
    try:
        current_index = promotion_hierarchy.index(current_tf)
    except ValueError:
        console.print(f"[red]Cannot promote from {timeframe}[/red]")
        raise typer.Exit(1)
    
    # Check if we can promote
    if current_index == 0:
        console.print(f"[yellow]Cannot promote from {format_timeframe_name(current_tf)} - already at shortest timeframe[/yellow]")
        raise typer.Exit(1)
    
    # Determine target timeframe
    target_tf = promotion_hierarchy[current_index - 1]
    
    # Perform the move
    target_name = format_timeframe_name(target_tf)
    console.print(f"[blue]Promoting tasks to {target_name}...[/blue]")
    
    # Reuse move command logic
    move(pattern, from_timeframe=timeframe, to_timeframe=target_tf.value.replace('_', ' ').replace('.md', '').replace('.txt', '').lower(), exact=exact, force=force)


@app.command()
def demote(
    pattern: str = typer.Argument(..., help="Task content or pattern to match"),
    timeframe: str = typer.Option(..., "--timeframe", "-t", help="Current timeframe: today, week, month, year, vomit"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    force: bool = typer.Option(False, "--force", "-f", help="Force demotion without confirmation")
):
    """Demote tasks to a longer timeframe (e.g., today → week)"""
    
    # Define demotion hierarchy (shorter to longer)
    demotion_hierarchy = [
        Timeframe.TODAY,
        Timeframe.WEEK,
        Timeframe.MONTH,
        Timeframe.YEAR,
        Timeframe.VOMIT
    ]
    
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    # Validate current timeframe
    if timeframe.lower() not in timeframe_map:
        console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
        console.print("Available timeframes: today, week, month, year, vomit")
        raise typer.Exit(1)
    
    current_tf = timeframe_map[timeframe.lower()]
    
    # Find current position in hierarchy
    try:
        current_index = demotion_hierarchy.index(current_tf)
    except ValueError:
        console.print(f"[red]Cannot demote from {timeframe}[/red]")
        raise typer.Exit(1)
    
    # Check if we can demote
    if current_index == len(demotion_hierarchy) - 1:
        console.print(f"[yellow]Cannot demote from {format_timeframe_name(current_tf)} - already at longest timeframe[/yellow]")
        raise typer.Exit(1)
    
    # Determine target timeframe
    target_tf = demotion_hierarchy[current_index + 1]
    
    # Perform the move
    target_name = format_timeframe_name(target_tf)
    console.print(f"[blue]Demoting tasks to {target_name}...[/blue]")
    
    # Reuse move command logic
    move(pattern, from_timeframe=timeframe, to_timeframe=target_tf.value.replace('_', ' ').replace('.md', '').replace('.txt', '').lower(), exact=exact, force=force)


@app.command()
def cleanup(
    timeframe: str = typer.Option(..., "--timeframe", "-t", help="Timeframe to cleanup: today, week, month, year, vomit"),
    completed_only: bool = typer.Option(True, "--completed-only", "-c", help="Only move completed tasks"),
    force: bool = typer.Option(False, "--force", "-f", help="Force cleanup without confirmation")
):
    """Clean up a timeframe by moving completed tasks to the next longer timeframe"""
    
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    # Validate timeframe
    if timeframe.lower() not in timeframe_map:
        console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
        console.print("Available timeframes: today, week, month, year, vomit")
        raise typer.Exit(1)
    
    current_tf = timeframe_map[timeframe.lower()]
    
    # Don't cleanup vomit
    if current_tf == Timeframe.VOMIT:
        console.print("[yellow]Cannot cleanup vomit timeframe[/yellow]")
        raise typer.Exit(1)
    
    # Define hierarchy to find next longer timeframe
    hierarchy = [Timeframe.TODAY, Timeframe.WEEK, Timeframe.MONTH, Timeframe.YEAR, Timeframe.VOMIT]
    current_index = hierarchy.index(current_tf)
    target_tf = hierarchy[current_index + 1]
    
    # Find tasks to cleanup
    file_ops = FileOperations()
    task_file = file_ops.read_task_file(current_tf)
    
    if completed_only:
        tasks_to_move = [task for task in task_file.tasks if task.completed]
    else:
        tasks_to_move = task_file.tasks
    
    if not tasks_to_move:
        console.print(f"[yellow]No tasks to cleanup in {format_timeframe_name(current_tf)}[/yellow]")
        return
    
    # Show tasks to be moved
    if not force:
        from_name = format_timeframe_name(current_tf)
        to_name = format_timeframe_name(target_tf)
        task_type = "completed" if completed_only else "all"
        
        console.print(f"[blue]Found {len(tasks_to_move)} {task_type} task(s) to cleanup from {from_name} to {to_name}:[/blue]")
        for i, task in enumerate(tasks_to_move[:10], 1):  # Show max 10
            status = "✓" if task.completed else "○"
            console.print(f"  {i}. {status} {task.content}")
        
        if len(tasks_to_move) > 10:
            console.print(f"  ... and {len(tasks_to_move) - 10} more")
        
        response = typer.confirm(f"Cleanup {len(tasks_to_move)} tasks?")
        if not response:
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Move tasks
    moved_count = 0
    for task in tasks_to_move:
        if move_task_to_timeframe(task, current_tf, target_tf):
            moved_count += 1
    
    # Show result
    from_name = format_timeframe_name(current_tf)
    to_name = format_timeframe_name(target_tf)
    
    if moved_count > 0:
        console.print(f"[green]✓[/green] Cleaned up {moved_count} task(s) from {from_name} to {to_name}")
    else:
        console.print(f"[red]No tasks were cleaned up[/red]")


if __name__ == "__main__":
    app()