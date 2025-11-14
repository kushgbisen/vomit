import pytest
from datetime import datetime
from core.models import Task, TaskFile, Timeframe


class TestTask:
    def test_task_creation(self):
        task = Task(content="Test task")
        assert task.content == "Test task"
        assert task.completed is False
        assert task.created_at is not None
        assert task.completed_at is None
    
    def test_task_completion(self):
        task = Task(content="Test task", completed=True)
        assert task.completed is True
    
    def test_task_to_markdown(self):
        # Incomplete task
        task = Task(content="Test task", completed=False)
        assert task.to_markdown() == "[ ] Test task"
        
        # Complete task
        task = Task(content="Test task", completed=True)
        assert task.to_markdown() == "[x] Test task"
    
    def test_task_from_markdown(self):
        # Complete task
        task = Task.from_markdown("[x] Test task")
        assert task is not None
        assert task.content == "Test task"
        assert task.completed is True
        
        # Incomplete task
        task = Task.from_markdown("[ ] Test task")
        assert task is not None
        assert task.content == "Test task"
        assert task.completed is False
        
        # Invalid format
        task = Task.from_markdown("Invalid task")
        assert task is None
        
        # Empty line
        task = Task.from_markdown("")
        assert task is None
        
        task = Task.from_markdown("   ")
        assert task is None


class TestTaskFile:
    def test_task_file_creation(self):
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        assert task_file.timeframe == Timeframe.TODAY
        assert len(task_file.tasks) == 0
    
    def test_add_task(self):
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        task = Task(content="Test task")
        
        task_file.add_task(task)
        assert len(task_file.tasks) == 1
        assert task_file.tasks[0] == task
    
    def test_remove_task(self):
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        task = Task(content="Test task")
        task_file.add_task(task)
        
        # Remove existing task
        result = task_file.remove_task("Test task")
        assert result is True
        assert len(task_file.tasks) == 0
        
        # Remove non-existing task
        result = task_file.remove_task("Non-existing task")
        assert result is False
    
    def test_find_tasks(self):
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        task1 = Task(content="Buy groceries")
        task2 = Task(content="Buy milk")
        task3 = Task(content="Walk dog")
        
        task_file.add_task(task1)
        task_file.add_task(task2)
        task_file.add_task(task3)
        
        # Find tasks with "buy"
        results = task_file.find_tasks("buy")
        assert len(results) == 2
        assert task1 in results
        assert task2 in results
        
        # Find tasks with "walk"
        results = task_file.find_tasks("walk")
        assert len(results) == 1
        assert task3 in results
        
        # Case insensitive search
        results = task_file.find_tasks("BUY")
        assert len(results) == 2
    
    def test_task_counts(self):
        task_file = TaskFile(timeframe=Timeframe.TODAY, tasks=[])
        task1 = Task(content="Task 1", completed=False)
        task2 = Task(content="Task 2", completed=True)
        task3 = Task(content="Task 3", completed=True)
        
        task_file.add_task(task1)
        task_file.add_task(task2)
        task_file.add_task(task3)
        
        assert task_file.get_total_count() == 3
        assert task_file.get_completed_count() == 2