import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typer.testing import CliRunner

from commands.status import app, calculate_progress, format_progress_bar, get_recently_completed, show_timeframe_status
from core.models import Task, TaskFile, Timeframe


class TestStatusCommand:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_calculate_progress(self):
        # Test with tasks
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Task 1", completed=True),
            Task(content="Task 2", completed=False),
            Task(content="Task 3", completed=True)
        ])
        
        completed, total, percentage = calculate_progress(task_file)
        assert completed == 2
        assert total == 3
        assert percentage == 66.66666666666666
        
        # Test with empty file
        empty_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        completed, total, percentage = calculate_progress(empty_file)
        assert completed == 0
        assert total == 0
        assert percentage == 0.0
    
    def test_format_progress_bar(self):
        # Test various percentages
        assert format_progress_bar(0.0) == "░░░░░░░░░░░░░░░░░░░░ 0.0%"
        assert format_progress_bar(50.0) == "██████████░░░░░░░░░ 50.0%"
        assert format_progress_bar(100.0) == "████████████████████ 100.0%"
        
        # Test custom width
        assert format_progress_bar(25.0, width=10) == "██░░░░░░░ 25.0%"
    
    def test_get_recently_completed(self):
        # Create tasks with different completion times
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Recent task", completed=True, completed_at=now),
            Task(content="Yesterday task", completed=True, completed_at=yesterday),
            Task(content="Week ago task", completed=True, completed_at=week_ago),
            Task(content="Old task", completed=True, completed_at=two_weeks_ago),
            Task(content="Incomplete task", completed=False)
        ])
        
        # Get tasks from last 7 days
        recent = get_recently_completed(task_file, days=7)
        assert len(recent) == 3  # Recent, yesterday, week ago
        
        # Check they are sorted by completion time (newest first)
        assert recent[0].content == "Recent task"
        assert recent[1].content == "Yesterday task"
        assert recent[2].content == "Week ago task"
    
    def test_status_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 2
            mock_task_file.get_total_count.return_value = 5
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["status", "--timeframe", "today"])
            assert result.exit_code == 0
            assert "Today" in result.stdout
    
    def test_status_command_all_timeframes(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 2
            mock_task_file.get_total_count.return_value = 5
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["status", "--all"])
            assert result.exit_code == 0
    
    def test_status_command_with_details(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            # Create mock tasks
            now = datetime.now()
            mock_task = MagicMock()
            mock_task.completed = True
            mock_task.completed_at = now
            mock_task.content = "Test task"
            
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 1
            mock_task_file.get_total_count.return_value = 2
            mock_task_file.tasks = [mock_task, MagicMock(completed=False, content="Incomplete task")]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["status", "--details"])
            assert result.exit_code == 0
    
    def test_status_command_summary(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 2
            mock_task_file.get_total_count.return_value = 5
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["status", "--summary"])
            assert result.exit_code == 0
            assert "Task Summary" in result.stdout
    
    def test_status_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["status", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_progress_command(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 3
            mock_task_file.get_total_count.return_value = 5
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["progress"])
            assert result.exit_code == 0
            assert "Task Progress" in result.stdout
    
    def test_progress_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 3
            mock_task_file.get_total_count.return_value = 5
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["progress", "--timeframe", "today"])
            assert result.exit_code == 0
    
    def test_overview_command(self, runner, temp_dir):
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 2
            mock_task_file.get_total_count.return_value = 4
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["overview"])
            assert result.exit_code == 0
            assert "Quick Overview" in result.stdout
    
    def test_show_timeframe_status_empty(self, temp_dir):
        # Test with empty timeframe
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 0
            mock_task_file.get_total_count.return_value = 0
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            # This should not raise an error
            show_timeframe_status(Timeframe.TODAY)
    
    def test_show_timeframe_status_with_tasks(self, temp_dir):
        # Test with tasks
        with patch('commands.status.FileOperations') as mock_file_ops:
            mock_task = MagicMock()
            mock_task.completed = True
            mock_task.completed_at = datetime.now()
            mock_task.content = "Completed task"
            
            mock_task_file = MagicMock()
            mock_task_file.get_completed_count.return_value = 1
            mock_task_file.get_total_count.return_value = 2
            mock_task_file.tasks = [mock_task, MagicMock(completed=False, content="Incomplete task")]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            show_timeframe_status(Timeframe.TODAY)
    
    def test_status_file_operations(self, temp_dir):
        # Test actual file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=True),
            Task(content="Buy milk", completed=False),
            Task(content="Walk dog", completed=True)
        ])
        file_ops.write_task_file(task_file)
        
        # Test calculate_progress with real file
        read_file = file_ops.read_task_file(Timeframe.TODAY)
        completed, total, percentage = calculate_progress(read_file)
        
        assert completed == 2
        assert total == 3
        assert percentage == 66.66666666666666
        
        # Test get_recently_completed with real file
        recent = get_recently_completed(read_file, days=7)
        assert len(recent) == 2
        assert all(task.completed for task in recent)