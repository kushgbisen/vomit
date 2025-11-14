import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from commands.add import app, detect_timeframe, add_task_to_timeframe
from core.models import Timeframe


class TestAddCommand:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_detect_timeframe(self):
        # Today keywords
        assert detect_timeframe("Buy milk today") == Timeframe.TODAY
        assert detect_timeframe("Call mom right now") == Timeframe.TODAY
        assert detect_timeframe("Finish report ASAP") == Timeframe.TODAY
        assert detect_timeframe("Read book tonight") == Timeframe.TODAY
        
        # Week keywords
        assert detect_timeframe("Apply for jobs this week") == Timeframe.WEEK
        assert detect_timeframe("Clean house by friday") == Timeframe.WEEK
        assert detect_timeframe("Plan trip weekend") == Timeframe.WEEK
        
        # Month keywords
        assert detect_timeframe("Learn Python this month") == Timeframe.MONTH
        assert detect_timeframe("Finish course in a month") == Timeframe.MONTH
        assert detect_timeframe("Start project next month") == Timeframe.MONTH
        
        # Year keywords
        assert detect_timeframe("Write book this year") == Timeframe.YEAR
        assert detect_timeframe("Learn guitar eventually") == Timeframe.YEAR
        assert detect_timeframe("Start business someday") == Timeframe.YEAR
        
        # No keywords
        assert detect_timeframe("Random task") is None
        assert detect_timeframe("Buy groceries") is None
    
    def test_add_task_to_timeframe(self, temp_dir):
        # Test adding valid task
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = add_task_to_timeframe("Buy groceries", Timeframe.TODAY)
            assert result is True
            
            # Check that write_task_file was called
            mock_file_ops.return_value.write_task_file.assert_called_once()
    
    def test_add_task_to_timeframe_invalid(self, temp_dir):
        # Test adding invalid task
        with patch('commands.add.FileOperations'):
            with patch('commands.add.console') as mock_console:
                result = add_task_to_timeframe("", Timeframe.TODAY)
                assert result is False
                mock_console.print.assert_called()
    
    def test_add_command_specific_timeframe(self, runner, temp_dir):
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = runner.invoke(app, ["add", "Buy groceries", "--timeframe", "today"])
            assert result.exit_code == 0
            assert "Added task to Today" in result.stdout
    
    def test_add_command_invalid_timeframe(self, runner):
        result = runner.invoke(app, ["add", "Buy groceries", "--timeframe", "invalid"])
        assert result.exit_code == 1
        assert "Invalid timeframe" in result.stdout
    
    def test_add_command_auto_detection(self, runner, temp_dir):
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = runner.invoke(app, ["add", "Buy milk today", "--auto"])
            assert result.exit_code == 0
            assert "Added task to Today" in result.stdout
    
    def test_add_command_auto_detection_fallback(self, runner, temp_dir):
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = runner.invoke(app, ["add", "Random task", "--auto"])
            assert result.exit_code == 0
            assert "Added task to Today" in result.stdout
            assert "Could not auto-detect timeframe" in result.stdout
    
    def test_add_command_default_timeframe(self, runner, temp_dir):
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = runner.invoke(app, ["add", "Buy groceries"])
            assert result.exit_code == 0
            assert "Added task to Today" in result.stdout
    
    def test_quick_command(self, runner, temp_dir):
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_file_ops.return_value.read_task_file.return_value.tasks = []
            mock_file_ops.return_value.write_task_file.return_value = None
            
            result = runner.invoke(app, ["quick", "Buy milk today"])
            assert result.exit_code == 0
            assert "Added task to Today" in result.stdout
    
    def test_add_task_validation(self, temp_dir):
        # Test adding non-actionable task
        with patch('commands.add.FileOperations'):
            with patch('commands.add.console') as mock_console:
                result = add_task_to_timeframe("note: remember this", Timeframe.TODAY)
                assert result is False
                mock_console.print.assert_called()
    
    def test_add_task_cleaning(self, temp_dir):
        # Test task content cleaning
        with patch('commands.add.FileOperations') as mock_file_ops:
            mock_task_file = mock_file_ops.return_value.read_task_file.return_value
            mock_task_file.tasks = []
            
            add_task_to_timeframe("  Buy groceries  ", Timeframe.TODAY)
            
            # Check that the task was added with cleaned content
            mock_task_file.add_task.assert_called_once()
            added_task = mock_task_file.add_task.call_args[0][0]
            assert added_task.content == "Buy groceries"