import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from commands.move import app, find_matching_tasks, validate_timeframe_move, move_task_to_timeframe, format_timeframe_name
from core.models import Task, TaskFile, Timeframe


class TestMoveCommand:
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
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[
            Task(content="Buy groceries"),
            Task(content="Buy milk"),
            Task(content="Walk dog")
        ])
        
        # Pattern match
        matches = find_matching_tasks(task_file, "buy", exact_match=False)
        assert len(matches) == 2
        assert all("buy" in task.content.lower() for task in matches)
    
    def test_validate_timeframe_move(self):
        # Valid moves
        assert validate_timeframe_move(Timeframe.TODAY, Timeframe.WEEK) is True
        assert validate_timeframe_move(Timeframe.WEEK, Timeframe.MONTH) is True
        
        # Invalid move (same timeframe)
        assert validate_timeframe_move(Timeframe.TODAY, Timeframe.TODAY) is False
    
    def test_format_timeframe_name(self):
        assert format_timeframe_name(Timeframe.TODAY) == "Today"
        assert format_timeframe_name(Timeframe.WEEK) == "Week"
        assert format_timeframe_name(Timeframe.MONTH) == "Month"
        assert format_timeframe_name(Timeframe.YEAR) == "Year"
        assert format_timeframe_name(Timeframe.VOMIT) == "Vomit"
    
    def test_move_task_to_timeframe(self, temp_dir):
        # Test actual file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create source file with task
        task = Task(content="Buy groceries", completed=False)
        source_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[task])
        file_ops.write_task_file(source_file)
        
        # Move task
        result = move_task_to_timeframe(task, Timeframe.TODAY, Timeframe.WEEK)
        assert result is True
        
        # Verify task was moved
        source_after = file_ops.read_task_file(Timeframe.TODAY)
        dest_after = file_ops.read_task_file(Timeframe.WEEK)
        
        assert len(source_after.tasks) == 0
        assert len(dest_after.tasks) == 1
        assert dest_after.tasks[0].content == "Buy groceries"
    
    def test_move_task_to_timeframe_task_not_found(self, temp_dir):
        # Test moving task that doesn't exist in source
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create empty source file
        source_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        file_ops.write_task_file(source_file)
        
        # Try to move non-existent task
        task = Task(content="Non-existent task", completed=False)
        result = move_task_to_timeframe(task, Timeframe.TODAY, Timeframe.WEEK)
        assert result is False
    
    def test_move_command_basic(self, runner, temp_dir):
        with patch('commands.move.FileOperations') as mock_file_ops:
            # Setup mock source file
            mock_source_file = MagicMock()
            mock_source_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_source_file.remove_task.return_value = True
            
            # Setup mock dest file
            mock_dest_file = MagicMock()
            mock_dest_file.tasks = []
            
            # Configure FileOperations mock
            file_ops_instance = mock_file_ops.return_value
            file_ops_instance.read_task_file.side_effect = lambda tf: (
                mock_source_file if tf == Timeframe.TODAY else mock_dest_file
            )
            
            with patch('commands.move.move_task_to_timeframe', return_value=True):
                result = runner.invoke(app, ["move", "Buy groceries", "--from", "today", "--to", "week", "--force"])
                assert result.exit_code == 0
                assert "Moved" in result.stdout
    
    def test_move_command_invalid_timeframes(self, runner):
        # Invalid source timeframe
        result = runner.invoke(app, ["move", "Buy groceries", "--from", "invalid", "--to", "week"])
        assert result.exit_code == 1
        assert "Invalid source timeframe" in result.stdout
        
        # Invalid destination timeframe
        result = runner.invoke(app, ["move", "Buy groceries", "--from", "today", "--to", "invalid"])
        assert result.exit_code == 1
        assert "Invalid destination timeframe" in result.stdout
    
    def test_move_command_same_timeframe(self, runner):
        result = runner.invoke(app, ["move", "Buy groceries", "--from", "today", "--to", "today"])
        assert result.exit_code == 1
        assert "Cannot move tasks" in result.stdout
    
    def test_move_command_no_matches(self, runner, temp_dir):
        with patch('commands.move.FileOperations') as mock_file_ops:
            mock_file = MagicMock()
            mock_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_file
            
            result = runner.invoke(app, ["move", "Non-existent", "--from", "today", "--to", "week"])
            assert result.exit_code == 1
            assert "No tasks found" in result.stdout
    
    def test_promote_command(self, runner, temp_dir):
        with patch('commands.move.move') as mock_move:
            mock_move.return_value = None
            
            result = runner.invoke(app, ["promote", "Buy groceries", "--timeframe", "week", "--force"])
            assert result.exit_code == 0
            # Check that move was called with correct parameters
            mock_move.assert_called_once()
    
    def test_promote_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["promote", "Buy groceries", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_promote_command_from_today(self, runner):
        # Can't promote from today (already shortest)
        result = runner.invoke(app, ["promote", "Buy groceries", "--timeframe", "today"])
        assert result.exit_code == 1
        assert "Cannot promote" in result.stdout
    
    def test_demote_command(self, runner, temp_dir):
        with patch('commands.move.move') as mock_move:
            mock_move.return_value = None
            
            result = runner.invoke(app, ["demote", "Buy groceries", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            # Check that move was called with correct parameters
            mock_move.assert_called_once()
    
    def test_demote_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["demote", "Buy groceries", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_demote_command_from_vomit(self, runner):
        # Can't demote from vomit (already longest)
        result = runner.invoke(app, ["demote", "Buy groceries", "--timeframe", "vomit"])
        assert result.exit_code == 1
        assert "Cannot demote" in result.stdout
    
    def test_cleanup_command(self, runner, temp_dir):
        with patch('commands.move.FileOperations') as mock_file_ops:
            mock_file = MagicMock()
            mock_file.tasks = [Task(content="Buy groceries", completed=True)]
            mock_file_ops.return_value.read_task_file.return_value = mock_file
            
            with patch('commands.move.move_task_to_timeframe', return_value=True):
                result = runner.invoke(app, ["cleanup", "--timeframe", "today", "--force"])
                assert result.exit_code == 0
                assert "Cleaned up" in result.stdout
    
    def test_cleanup_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["cleanup", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_cleanup_command_vomit(self, runner):
        # Can't cleanup vomit
        result = runner.invoke(app, ["cleanup", "--timeframe", "vomit"])
        assert result.exit_code == 1
        assert "Cannot cleanup vomit" in result.stdout
    
    def test_cleanup_command_no_tasks(self, runner, temp_dir):
        with patch('commands.move.FileOperations') as mock_file_ops:
            mock_file = MagicMock()
            mock_file.tasks = []
            mock_file_ops.return_value.read_task_file.return_value = mock_file
            
            result = runner.invoke(app, ["cleanup", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "No tasks to cleanup" in result.stdout
    
    def test_cleanup_command_incomplete_tasks(self, runner, temp_dir):
        with patch('commands.move.FileOperations') as mock_file_ops:
            mock_file = MagicMock()
            mock_file.tasks = [Task(content="Buy groceries", completed=False)]
            mock_file_ops.return_value.read_task_file.return_value = mock_file
            
            # With completed_only=True (default), should not find tasks
            result = runner.invoke(app, ["cleanup", "--timeframe", "today", "--force"])
            assert result.exit_code == 0
            assert "No tasks to cleanup" in result.stdout
    
    def test_move_file_operations_integration(self, temp_dir):
        # Full integration test with real file operations
        file_ops = FileOperations(base_dir=temp_dir)
        
        # Create source and destination files
        source_task = Task(content="Buy groceries", completed=True)
        other_task = Task(content="Other task", completed=False)
        
        source_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[source_task, other_task])
        dest_file = TaskFile(timeframe=Timeframe.WEEK, tasks=[])
        
        file_ops.write_task_file(source_file)
        file_ops.write_task_file(dest_file)
        
        # Move the task
        result = move_task_to_timeframe(source_task, Timeframe.TODAY, Timeframe.WEEK)
        assert result is True
        
        # Verify the move
        updated_source = file_ops.read_task_file(Timeframe.TODAY)
        updated_dest = file_ops.read_task_file(Timeframe.WEEK)
        
        assert len(updated_source.tasks) == 1
        assert len(updated_dest.tasks) == 1
        assert updated_source.tasks[0].content == "Other task"
        assert updated_dest.tasks[0].content == "Buy groceries"
        assert updated_dest.tasks[0].completed is True  # Status should be preserved