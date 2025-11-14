import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from commands.remove import app, find_matching_tasks, remove_task_from_timeframe
from core.models import Task, Timeframe


class TestRemoveCommand:
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
        
        # Case insensitive
        matches = find_matching_tasks(task_file, "BUY", exact_match=False)
        assert len(matches) == 2
    
    def test_remove_task_from_timeframe(self, temp_dir):
        # Create task file with tasks
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [
                Task(content="Buy groceries"),
                Task(content="Buy milk"),
                Task(content="Walk dog")
            ]
            mock_task_file.remove_task.return_value = True
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            # Test removal with force
            removed = remove_task_from_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True)
            assert removed > 0
            
            # Verify remove_task was called
            mock_task_file.remove_task.assert_called()
    
    def test_remove_task_from_timeframe_no_matches(self, temp_dir):
        # Test with no matching tasks
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            removed = remove_task_from_timeframe("Buy", Timeframe.TODAY, exact_match=False, force=True)
            assert removed == 0
    
    def test_remove_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries")]
            mock_task_file.remove_task.return_value = True
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["remove", "Buy groceries", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "Removed" in result.stdout
    
    def test_remove_command_all_timeframes(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries")]
            mock_task_file.remove_task.return_value = True
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["remove", "Buy groceries", "--all", "--force"])
            assert result.exit_code == 0
            assert "Removed" in result.stdout
    
    def test_remove_command_exact_match(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries")]
            mock_task_file.remove_task.return_value = True
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["remove", "Buy groceries", "--exact", "--force"])
            assert result.exit_code == 0
    
    def test_remove_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["remove", "Buy groceries", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_remove_command_no_matches(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["remove", "Buy groceries", "--force"])
            assert result.exit_code == 0
            assert "No tasks found" in result.stdout
    
    def test_clear_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries"), Task(content="Buy milk")]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["clear", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "Cleared" in result.stdout
    
    def test_clear_command_all_timeframes(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = [Task(content="Buy groceries")]
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["clear", "--all", "--force"])
            assert result.exit_code == 0
            assert "Cleared" in result.stdout
    
    def test_clear_command_empty_timeframe(self, runner, temp_dir):
        with patch('commands.remove.FileOperations') as mock_file_ops:
            mock_task_file = MagicMock()
            mock_task_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_task_file
            
            result = runner.invoke(app, ["clear", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "No tasks to clear" in result.stdout
    
    def test_clear_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["clear", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_remove_task_file_operations(self, temp_dir):
        # Test actual file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        file_ops.write_task_file(task_file)
        
        # Remove task
        removed = remove_task_from_timeframe("Buy milk", Timeframe.TODAY, exact_match=True, force=True)
        assert removed == 1
        
        # Verify task was removed
        updated_file = file_ops.read_task_file(Timeframe.TODAY)
        assert len(updated_file.tasks) == 2
        assert all(task.content != "Buy milk" for task in updated_file.tasks)
    
    def test_clear_file_operations(self, temp_dir):
        # Test actual file operations for clear
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create a task file
        from core.models import TaskFile
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk")
        ])
        file_ops.write_task_file(task_file)
        
        # Clear tasks
        with patch('commands.remove.typer.confirm', return_value=True):
            with patch('commands.remove.FileOperations', return_value=file_ops):
                runner = CliRunner()
                result = runner.invoke(app, ["clear", "--timeframe", "today"])
                assert result.exit_code == 0
        
        # Verify tasks were cleared
        updated_file = file_ops.read_task_file(Timeframe.TODAY)
        assert len(updated_file.tasks) == 0