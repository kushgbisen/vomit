import typer
from typing import Optional
from rich.console import Console
from rich.text import Text

from core.models import Task, Timeframe
from core.file_ops import FileOperations
from core.validator import TaskValidator

app = typer.Typer(help="Add tasks to different timeframes")
console = Console()

# Timeframe keywords for auto-categorization
TIMEFRAME_KEYWORDS = {
    Timeframe.TODAY: ["today", "now", "immediate", "asap", "tonight", "right now"],
    Timeframe.WEEK: ["week", "this week", "few days", "weekend", "by friday", "in a week"],
    Timeframe.MONTH: ["month", "this month", "few weeks", "next month", "in a month"],
    Timeframe.YEAR: ["year", "this year", "long-term", "eventually", "someday", "in a year"]
}


def detect_timeframe(content: str) -> Optional[Timeframe]:
    """Auto-detect timeframe based on keywords in content"""
    content_lower = content.lower()
    
    for timeframe, keywords in TIMEFRAME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content_lower:
                return timeframe
    
    return None


def add_task_to_timeframe(content: str, timeframe: Timeframe, validate: bool = True) -> bool:
    """Add a task to a specific timeframe file"""
    if validate:
        validator = TaskValidator()
        cleaned_content, error = validator.validate_and_clean_task(content, require_actionable=True)
        if error:
            console.print(f"[red]Error: {error}[/red]")
            return False
        content = cleaned_content
    
    # Create task object
    task = Task(content=content, completed=False)
    
    # Read existing tasks
    file_ops = FileOperations()
    task_file = file_ops.read_task_file(timeframe)
    
    # Add new task
    task_file.add_task(task)
    
    # Write back to file
    file_ops.write_task_file(task_file)
    
    return True


@app.command()
def add(
    content: str = typer.Argument(..., help="Task content to add"),
    timeframe: Optional[str] = typer.Option(None, "--timeframe", "-t", help="Timeframe: today, week, month, year"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-detect timeframe from keywords")
):
    """Add a task to a specific timeframe"""
    
    # Map timeframe string to enum
    timeframe_map = {
        "today": Timeframe.TODAY,
        "week": Timeframe.WEEK,
        "month": Timeframe.MONTH,
        "year": Timeframe.YEAR,
        "vomit": Timeframe.VOMIT
    }
    
    target_timeframe = None
    
    if timeframe:
        if timeframe.lower() not in timeframe_map:
            console.print(f"[red]Invalid timeframe: {timeframe}[/red]")
            console.print("Available timeframes: today, week, month, year, vomit")
            raise typer.Exit(1)
        target_timeframe = timeframe_map[timeframe.lower()]
    elif auto:
        target_timeframe = detect_timeframe(content)
        if not target_timeframe:
            console.print("[yellow]Could not auto-detect timeframe. Using 'today' as default.[/yellow]")
            target_timeframe = Timeframe.TODAY
    else:
        # Default to today if no timeframe specified
        target_timeframe = Timeframe.TODAY
    
    # Add the task
    success = add_task_to_timeframe(content, target_timeframe)
    
    if success:
        timeframe_name = target_timeframe.value.replace('_', ' ').replace('.md', '').replace('.txt', '').replace('1 ', '').replace('2 ', '').replace('3 ', '').replace('4 ', '').replace('5 ', '').strip().title()
        console.print(f"[green]✓[/green] Added task to {timeframe_name}: [cyan]{content}[/cyan]")
    else:
        console.print("[red]Failed to add task[/red]")
        raise typer.Exit(1)


@app.command()
def quick(
    content: str = typer.Argument(..., help="Quick task content"),
):
    """Quick add task with auto-detection"""
    add(content, timeframe=None, auto=True)


if __name__ == "__main__":
    app()