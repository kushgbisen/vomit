import pytest
import tempfile
import shutil
from pathlib import Path
from core.file_ops import FileOperations
from core.models import Task, TaskFile, Timeframe


class TestFileOperations:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_ops(self, temp_dir):
        return FileOperations(base_dir=temp_dir)
    
    def test_get_file_path(self, file_ops, temp_dir):
        path = file_ops.get_file_path(Timeframe.TODAY)
        expected = Path(temp_dir) / "_2_today.md"
        assert path == expected
    
    def test_read_nonexistent_file(self, file_ops):
        task_file = file_ops.read_task_file(Timeframe.TODAY)
        assert task_file.timeframe == Timeframe.TODAY
        assert len(task_file.tasks) == 0
    
    def test_write_and_read_task_file(self, file_ops):
        # Create task file with tasks
        task1 = Task(content="Task 1", completed=False)
        task2 = Task(content="Task 2", completed=True)
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[task1, task2])
        
        # Write to file
        file_ops.write_task_file(task_file)
        
        # Read back
        read_task_file = file_ops.read_task_file(Timeframe.TODAY)
        assert len(read_task_file.tasks) == 2
        assert read_task_file.tasks[0].content == "Task 1"
        assert read_task_file.tasks[0].completed is False
        assert read_task_file.tasks[1].content == "Task 2"
        assert read_task_file.tasks[1].completed is True
    
    def test_append_to_file(self, file_ops):
        # Append content
        file_ops.append_to_file(Timeframe.VOMIT, "Random note")
        file_ops.append_to_file(Timeframe.VOMIT, "Another note")
        
        # Read file content
        file_path = file_ops.get_file_path(Timeframe.VOMIT)
        with open(file_path, 'r') as f:
            content = f.read()
        
        assert "Random note\n" in content
        assert "Another note\n" in content
    
    def test_clear_file(self, file_ops):
        # Create file with content
        file_ops.append_to_file(Timeframe.TODAY, "[ ] Task 1")
        file_ops.append_to_file(Timeframe.TODAY, "[ ] Task 2")
        
        # Verify file exists and has content
        assert file_ops.file_exists(Timeframe.TODAY)
        
        # Clear file
        file_ops.clear_file(Timeframe.TODAY)
        
        # Verify file is empty
        task_file = file_ops.read_task_file(Timeframe.TODAY)
        assert len(task_file.tasks) == 0
    
    def test_file_exists(self, file_ops):
        # Non-existent file
        assert file_ops.file_exists(Timeframe.TODAY) is False
        
        # Create file
        file_ops.create_file_if_not_exists(Timeframe.TODAY)
        assert file_ops.file_exists(Timeframe.TODAY) is True
    
    def test_create_file_if_not_exists(self, file_ops):
        # File doesn't exist
        assert file_ops.file_exists(Timeframe.TODAY) is False
        
        # Create file
        file_ops.create_file_if_not_exists(Timeframe.TODAY)
        assert file_ops.file_exists(Timeframe.TODAY) is True
        
        # Call again (should not error)
        file_ops.create_file_if_not_exists(Timeframe.TODAY)
        assert file_ops.file_exists(Timeframe.TODAY) is True
    
    def test_backup_file(self, file_ops):
        # Create original file
        task1 = Task(content="Task 1")
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[task1])
        file_ops.write_task_file(task_file)
        
        # Create backup
        result = file_ops.backup_file(Timeframe.TODAY)
        assert result is True
        
        # Check backup file exists
        backup_path = file_ops.get_file_path(Timeframe.TODAY).with_suffix(".md.backup")
        assert backup_path.exists()
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            content = f.read()
        assert "[ ] Task 1" in content
    
    def test_backup_nonexistent_file(self, file_ops):
        # Try to backup non-existent file
        result = file_ops.backup_file(Timeframe.TODAY)
        assert result is False