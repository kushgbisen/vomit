import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typer.testing import CliRunner

from commands.search import app, search_tasks_in_file, search_by_regex, search_by_status, search_by_date, format_timeframe_name
from core.models import Task, TaskFile, Timeframe


class TestSearchCommand:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_search_tasks_in_file_partial_match(self):
        # Create task file with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        
        # Partial match
        matches = search_tasks_in_file(task_file, "buy", exact_match=False)
        assert len(matches) == 2
        assert all("buy" in task.content.lower() for task in matches)
        
        # Case insensitive
        matches = search_tasks_in_file(task_file, "BUY", exact_match=False, case_sensitive=False)
        assert len(matches) == 2
    
    def test_search_tasks_in_file_exact_match(self):
        # Create task file with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        
        # Exact match
        matches = search_tasks_in_file(task_file, "Buy groceries", exact_match=True)
        assert len(matches) == 1
        assert matches[0].content == "Buy groceries"
        
        # No exact match
        matches = search_tasks_in_file(task_file, "Buy", exact_match=True)
        assert len(matches) == 0
    
    def test_search_tasks_in_file_case_sensitive(self):
        # Create task file with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="buy milk"),
            Task(content="Walk dog")
        ])
        
        # Case sensitive
        matches = search_tasks_in_file(task_file, "Buy", exact_match=False, case_sensitive=True)
        assert len(matches) == 1
        assert matches[0].content == "Buy groceries"
        
        # Case insensitive
        matches = search_tasks_in_file(task_file, "Buy", exact_match=False, case_sensitive=False)
        assert len(matches) == 2
    
    def test_search_by_regex(self):
        # Create task file with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog"),
            Task(content="Call mom")
        ])
        
        # Regex pattern
        matches = search_by_regex(task_file, r"Buy \w+")
        assert len(matches) == 2
        
        # Invalid regex
        matches = search_by_regex(task_file, r"[invalid")
        assert len(matches) == 0
    
    def test_search_by_status(self):
        # Create task file with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=True),
            Task(content="Buy milk", completed=False),
            Task(content="Walk dog", completed=True)
        ])
        
        # Completed tasks
        matches = search_by_status(task_file, completed=True)
        assert len(matches) == 2
        assert all(task.completed for task in matches)
        
        # Incomplete tasks
        matches = search_by_status(task_file, completed=False)
        assert len(matches) == 1
        assert not matches[0].completed
        
        # All tasks
        matches = search_by_status(task_file, completed=None)
        assert len(matches) == 3
    
    def test_search_by_date(self):
        # Create task file with tasks
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Recent task", completed=True, completed_at=now),
            Task(content="Yesterday task", completed=True, completed_at=yesterday),
            Task(content="Old task", completed=True, completed_at=week_ago),
            Task(content="Incomplete task", completed=False)
        ])
        
        # Search by days (completed only)
        matches = search_by_date(task_file, days=3, completed_only=True)
        assert len(matches) == 2  # Recent and yesterday
        
        # Search by days (including incomplete)
        matches = search_by_date(task_file, days=3, completed_only=False)
        assert len(matches) == 0  # None created in last 3 days
    
    def test_format_timeframe_name(self):
        assert format_timeframe_name(Timeframe.TODAY) == "Today"
        assert format_timeframe_name(Timeframe.WEEK) == "Week"
        assert format_timeframe_name(Timeframe.MONTH) == "Month"
        assert format_timeframe_name(Timeframe.YEAR) == "Year"
        assert format_timeframe_name(Timeframe.VOMIT) == "Vomit"
    
    def test_search_command_basic(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [
                Task(content="Buy groceries", completed=False),
                Task(content="Buy milk", completed=False)
            ]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", "Buy"])
            assert result.exit_code == 0
            assert "Search Results" in result.stdout
    
    def test_search_command_exact_match(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", "Buy groceries", "--exact"])
            assert result.exit_code == 0
    
    def test_search_command_case_sensitive(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", "Buy", "--case-sensitive"])
            assert result.exit_code == 0
    
    def test_search_command_regex(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", r"Buy \w+", "--regex"])
            assert result.exit_code == 0
    
    def test_search_command_with_status_filter(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=True)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", "Buy", "--status", "completed"])
            assert result.exit_code == 0
    
    def test_search_command_with_days_filter(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task = MagicMock()
            mock_task.completed = True
            mock_task.completed_at = datetime.now()
            mock_task.content = "Buy groceries"
            
            mock_task_file = MagicMock()
            mock_task_file.tasks = [mock_task]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["search", "Buy", "--days", "7"])
            assert result.exit_code == 0
    
    def test_search_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["search", "Buy", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_search_command_invalid_status(self, runner):
        result = runner.invoke(app, ["search", "Buy", "--status", "invalid"])
        assert result.exit_code == 1
        assert "Invalid status" in result.stdout
    
    def test_find_command(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["find", "Buy"])
            assert result.exit_code == 0
            assert "Search Results" in result.stdout
    
    def test_completed_command(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task = MagicMock()
            mock_task.completed = True
            mock_task.completed_at = datetime.now()
            mock_task.content = "Buy groceries"
            
            mock_task_file = MagicMock()
            mock_task_file.tasks = [mock_task]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["completed"])
            assert result.exit_code == 0
            assert "Search Results" in result.stdout
    
    def test_incomplete_command(self, runner, temp_dir):
        with patch('commands.search.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["incomplete"])
            assert result.exit_code == 0
            assert "Search Results" in result.stdout
    
    def test_search_file_operations(self, temp_dir):
        # Test actual file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=True),
            Task(content="Buy milk", completed=False),
            Task(content="Walk dog", completed=True),
            Task(content="Call mom", completed=False)
        ])
        file_ops.write_task_file(task_file)
        
        # Test search with real file
        read_file = file_ops.read_task_file(Timeframe.TODAY)
        
        # Partial match
        matches = search_tasks_in_file(read_file, "buy", exact_match=False)
        assert len(matches) == 2
        
        # Exact match
        matches = search_tasks_in_file(read_file, "Buy groceries", exact_match=True)
        assert len(matches) == 1
        
        # Status search
        matches = search_by_status(read_file, completed=True)
        assert len(matches) == 2
        
        matches = search_by_status(read_file, completed=False)
        assert len(matches) == 2