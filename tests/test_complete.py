import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
from typer.testing import CliRunner

from commands.complete import app, find_matching_tasks, toggle_task_completion, complete_task_in_timeframe
from core.models import Task, Timeframe


class TestCompleteCommand:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_find_matching_tasks_exact(self):
        # Create task file with tasks
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        
        # Exact match
        matches = find_matching_tasks(task_file, "Buy groceries", exact_match=True)
        assert len(matches) == 1
        assert matches[0].content == "Buy groceries"
        
        # No exact match
        matches = find_matching_tasks(task_file, "Buy", exact_match=True)
        assert len(matches) == 0
    
    def test_find_matching_tasks_pattern(self):
        # Create task file with tasks
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        
        # Pattern match
        matches = find_matching_tasks(task_file, "buy", exact_match=False)
        assert len(matches) == 2
        assert all("buy" in task.content.lower() for task in matches)
    
    def test_toggle_task_completion(self):
        # Test completing an incomplete task
        task = Task(content="Buy groceries", completed=False)
        result = toggle_task_completion(task)
        assert result is True
        assert task.completed is True
        assert task.completed_at is not None
        
        # Test uncompleting a complete task
        result = toggle_task_completion(task)
        assert result is False
        assert task.completed is False
        assert task.completed_at is None
    
    def test_complete_task_in_timeframe(self, temp_dir):
        # Test completing tasks
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [
                Task(content="Buy groceries", completed=False),
                Task(content="Buy milk", completed=False)
            ]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            completed = complete_task_in_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True)
            assert completed == 2
            
            # Verify tasks were marked as completed
            for task in mock_task_file.tasks:
                assert task.completed is True
    
    def test_complete_task_in_timeframe_already_completed(self, temp_dir):
        # Test with already completed tasks
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [
                Task(content="Buy groceries", completed=True),
                Task(content="Buy milk", completed=True)
            ]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            completed = complete_task_in_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True)
            assert completed == 0  # No tasks to complete
    
    def test_uncomplete_task_in_timeframe(self, temp_dir):
        # Test uncompleting tasks
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [
                Task(content="Buy groceries", completed=True),
                Task(content="Buy milk", completed=False)
            ]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            uncompleted = complete_task_in_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True, uncomplete=True)
            assert uncompleted == 1  # Only one task was completed to begin with
    
    def test_complete_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["complete", "Buy groceries", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "Completed" in result.stdout
    
    def test_complete_command_all_timeframes(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["complete", "Buy groceries", "--all", "--force"])
            assert result.exit_code == 0
            assert "Completed" in result.stdout
    
    def test_complete_command_exact_match(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["complete", "Buy groceries", "--exact", "--force"])
            assert result.exit_code == 0
    
    def test_complete_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["complete", "Buy groceries", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_complete_command_no_matches(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["complete", "Buy groceries", "--force"])
            assert result.exit_code == 0
            assert "No tasks found" in result.stdout
    
    def test_uncomplete_command(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=True)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["uncomplete", "Buy groceries", "--force"])
            assert result.exit_code == 0
            assert "Uncompleted" in result.stdout
    
    def test_toggle_command(self, runner, temp_dir):
        with patch('commands.complete.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["toggle", "Buy groceries", "--force"])
            assert result.exit_code == 0
            assert "Toggled" in result.stdout
    
    def test_complete_file_operations(self, temp_dir):
        # Test actual file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=False),
            Task(content="Buy milk", completed=False),
            Task(content="Walk dog", completed=True)
        ])
        file_ops.write_task_file(task_file)
        
        # Complete tasks
        completed = complete_task_in_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True)
        assert completed == 2
        
        # Verify tasks were completed
        updated_file = file_ops.read_task_file(Timeframe.TODAY)
        buy_groceries = next(task for task in updated_file.tasks if task.content == "Buy groceries")
        buy_milk = next(task for task in updated_file.tasks if task.content == "Buy milk")
        walk_dog = next(task for task in updated_file.tasks if task.content == "Walk dog")
        
        assert buy_groceries.completed is True
        assert buy_milk.completed is True
        assert walk_dog.completed is True  # Should remain completed
    
    def test_uncomplete_file_operations(self, temp_dir):
        # Test actual file operations for uncomplete
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=True),
            Task(content="Buy milk", completed=False)
        ])
        file_ops.write_task_file(task_file)
        
        # Uncomplete tasks
        uncompleted = complete_task_in_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True, uncomplete=True)
        assert uncompleted == 1
        
        # Verify task was uncompleted
        updated_file = file_ops.read_task_file(Timeframe.TODAY)
        buy_groceries = next(task for task in updated_file.tasks if task.content == "Buy groceries")
        buy_milk = next(task for task in updated_file.tasks if task.content == "Buy milk")
        
        assert buy_groceries.completed is False
        assert buy_milk.completed is False  # Should remain incomplete
    
    def test_toggle_file_operations(self, temp_dir):
        # Test actual file operations for toggle
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries", completed=False),
            Task(content="Buy milk", completed=True)
        ])
        file_ops.write_task_file(task_file)
        
        # Toggle tasks
        with patch('commands.complete.FileOperations', return_value=file_ops):
            runner = CliRunner()
            result = runner.invoke(app, ["toggle", "Buy", "--force"])
            assert result.exit_code == 0
        
        # Verify tasks were toggled
        updated_file = file_ops.read_task_file(Timeframe.TODAY)
        buy_groceries = next(task for task in updated_file.tasks if task.content == "Buy groceries")
        buy_milk = next(task for task in updated_file.tasks if task.content == "Buy milk")
        
        assert buy_groceries.completed is True  # Was incomplete, now complete
        assert buy_milk.completed is False  # Was complete, now incomplete