import typer
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations

app = typer.Typer(help="Search tasks across timeframes")
console = Console()


def search_tasks_in_file(task_file, pattern: str, exact_match: bool = False, case_sensitive: bool = False) -> List[Task]:
    """Search for tasks matching pattern in a task file"""
    if not pattern:
        return []
    
    matching_tasks = []
    
    for task in task_file.tasks:
        task_content = task.content
        
        if not case_sensitive:
            task_content = task_content.lower()
            search_pattern = pattern.lower()
        else:
            search_pattern = pattern
        
        if exact_match:
            if task_content == search_pattern:
                matching_tasks.append(task)
        else:
            if search_pattern in task_content:
                matching_tasks.append(task)
    
    return matching_tasks


def search_by_regex(task_file, regex_pattern: str) -> List[Task]:
    """Search for tasks matching a regex pattern"""
    try:
        pattern = re.compile(regex_pattern)
    except re.error as e:
        console.print(f"[red]Invalid regex pattern: {e}[/red]")
        return []
    
    matching_tasks = []
    for task in task_file.tasks:
        if pattern.search(task.content):
            matching_tasks.append(task)
    
    return matching_tasks


def search_by_status(task_file, completed: Optional[bool] = None) -> List[Task]:
    """Search for tasks by completion status"""
    if completed is None:
        return task_file.tasks
    
    return [task for task in task_file.tasks if task.completed == completed]


def search_by_date(task_file, days: Optional[int] = None, completed_only: bool = True) -> List[Task]:
    """Search for tasks by completion/completion date"""
    if days is None:
        return task_file.tasks
    
    cutoff_date = datetime.now() - timedelta(days=days)
    matching_tasks = []
    
    for task in task_file.tasks:
        if completed_only and not task.completed:
            continue
        
        if task.completed and task.completed_at and task.completed_at >= cutoff_date:
            matching_tasks.append(task)
        elif not completed_only and task.created_at and task.created_at >= cutoff_date:
            matching_tasks.append(task)
    
    return matching_tasks


def format_timeframe_name(timeframe: Timeframe) -> str:
    """Format timeframe name for display"""
    return timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()


def display_search_results(results: Dict[Timeframe, List[Task]], show_timeframe: bool = True, show_status: bool = True, show_date: bool = False):
    """Display search results in a formatted table"""
    if not results or all(not tasks for tasks in results.values()):
        console.print("[yellow]No tasks found matching your search criteria[/yellow]")
        return
    
    # Create table
    table = Table(title="🔍 Search Results", show_header=True, header_style="bold blue")
    
    # Add columns
    if show_timeframe:
        table.add_column("Timeframe", style="cyan", width=12)
    table.add_column("Task", style="white", width=50)
    if show_status:
        table.add_column("Status", style="green", width=8)
    if show_date:
        table.add_column("Date", style="yellow", width=12)
    
    total_results = 0
    
    for timeframe, tasks in results.items():
        for task in tasks:
            row_data = []
            
            if show_timeframe:
                row_data.append(format_timeframe_name(timeframe))
            
            # Task content with highlighting (simplified)
            row_data.append(task.content)
            
            if show_status:
                status = "✓" if task.completed else "○"
                row_data.append(status)
            
            if show_date:
                if task.completed and task.completed_at:
                    date_str = task.completed_at.strftime("%Y-%m-%d")
                elif task.created_at:
                    date_str = task.created_at.strftime("%Y-%m-%d")
                else:
                    date_str = "Unknown"
                row_data.append(date_str)
            
            table.add_row(*row_data)
            total_results += 1
    
    console.print(table)
    console.print(f"\n[dim]Found {total_results} task(s) total[/dim]")


def aggregate_search_results(timeframes: List[Timeframe], pattern: str, exact_match: bool = False, case_sensitive: bool = False) -> Dict[Timeframe, List[Task]]:
    """Search across multiple timeframes and aggregate results"""
    file_ops = FileOperations()
    results = {}
    
    for timeframe in timeframes:
        task_file = file_ops.read_task_file(timeframe)
        matching_tasks = search_tasks_in_file(task_file, pattern, exact_match, case_sensitive)
        
        if matching_tasks:
            results[timeframe] = matching_tasks
    
    return results


@app.command()
def search(
    pattern: str = typer.Argument(..., help="Search pattern"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    exact: bool = typer.Option(False, "--exact", "-e", help="Exact match only"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case sensitive search"),
    regex: bool = typer.Option(False, "--regex", "-r", help="Use regex pattern"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status: completed, incomplete"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="Filter by days (completed tasks only)"),
    show_date: bool = typer.Option(False, "--show-date", help="Show completion dates")
):
    """Search for tasks across timeframes"""
    
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
        # Default to all timeframes for search
        target_timeframes = list(Timeframe)
    
    file_ops = FileOperations()
    results = {}
    
    for tf in target_timeframes:
        task_file = file_ops.read_task_file(tf)
        matching_tasks = []
        
        # Apply search filters
        if regex:
            matching_tasks = search_by_regex(task_file, pattern)
        else:
            matching_tasks = search_tasks_in_file(task_file, pattern, exact, case_sensitive)
        
        # Apply additional filters
        if status:
            if status.lower() == "completed":
                matching_tasks = [task for task in matching_tasks if task.completed]
            elif status.lower() == "incomplete":
                matching_tasks = [task for task in matching_tasks if not task.completed]
            else:
                console.print(f"[red]Invalid status: {status}[/red]")
                console.print("Available statuses: completed, incomplete")
                raise typer.Exit(1)
        
        if days is not None:
            matching_tasks = [task for task in matching_tasks 
                           if task.completed and task.completed_at and 
                           (datetime.now() - task.completed_at).days <= days]
        
        if matching_tasks:
            results[tf] = matching_tasks
    
    # Display results
    display_search_results(results, show_timeframe=len(target_timeframes) > 1, show_date=show_date)


@app.command()
def find(
    pattern: str = typer.Argument(..., help="Search pattern"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes")
):
    """Quick search (case-insensitive, partial match)"""
    search(pattern, timeframe, all_timeframes, exact=False, case_sensitive=False)


@app.command()
def completed(
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="Filter by days"),
    show_date: bool = typer.Option(True, "--show-date", help="Show completion dates")
):
    """Show completed tasks"""
    
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
        target_timeframes = [Timeframe.TODAY]
    
    file_ops = FileOperations()
    results = {}
    
    for tf in target_timeframes:
        task_file = file_ops.read_task_file(tf)
        matching_tasks = search_by_status(task_file, completed=True)
        
        if days is not None:
            matching_tasks = [task for task in matching_tasks 
                           if task.completed and task.completed_at and 
                           (datetime.now() - task.completed_at).days <= days]
        
        if matching_tasks:
            results[tf] = matching_tasks
    
    display_search_results(results, show_timeframe=len(target_timeframes) > 1, show_status=False, show_date=show_date)


@app.command()
def incomplete(
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year, vomit"),
    all_timeframes: bool = typer.Option(False, "--all", "-a", help="Search all timeframes")
):
    """Show incomplete tasks"""
    
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
        target_timeframes = [Timeframe.TODAY]
    
    file_ops = FileOperations()
    results = {}
    
    for tf in target_timeframes:
        task_file = file_ops.read_task_file(tf)
        matching_tasks = search_by_status(task_file, completed=False)
        
        if matching_tasks:
            results[tf] = matching_tasks
    
    display_search_results(results, show_timeframe=len(target_timeframes) > 1, show_status=False)


if __name__ == "__main__":
    app()