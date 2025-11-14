import pytest
from core.validator import TaskValidator, ValidationError
from core.models import Task


class TestTaskValidator:
    @pytest.fixture
    def validator(self):
        return TaskValidator()
    
    def test_validate_task_content_valid(self, validator):
        # Valid content
        is_valid, error = validator.validate_task_content("Buy groceries")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validator.validate_task_content("  Read book  ")
        assert is_valid is True
        assert error is None
    
    def test_validate_task_content_invalid(self, validator):
        # Empty content
        is_valid, error = validator.validate_task_content("")
        assert is_valid is False
        assert "cannot be empty" in error
        
        is_valid, error = validator.validate_task_content("   ")
        assert is_valid is False
        assert "cannot be empty" in error
        
        # Newline character
        is_valid, error = validator.validate_task_content("Task\nwith newline")
        assert is_valid is False
        assert "cannot contain" in error
        
        # Tab character
        is_valid, error = validator.validate_task_content("Task\twith tab")
        assert is_valid is False
        assert "cannot contain" in error
        
        # Too long content
        long_content = "a" * 501
        is_valid, error = validator.validate_task_content(long_content)
        assert is_valid is False
        assert "cannot exceed" in error
    
    def test_validate_task_format_valid(self, validator):
        # Valid incomplete task
        is_valid, error = validator.validate_task_format("[ ] Buy groceries")
        assert is_valid is True
        assert error is None
        
        # Valid complete task
        is_valid, error = validator.validate_task_format("[x] Read book")
        assert is_valid is True
        assert error is None
        
        # With extra spaces
        is_valid, error = validator.validate_task_format("[ ]   Multiple spaces   ")
        assert is_valid is True
        assert error is None
    
    def test_validate_task_format_invalid(self, validator):
        # Missing checkbox
        is_valid, error = validator.validate_task_format("Buy groceries")
        assert is_valid is False
        assert "must start with" in error
        
        # Wrong checkbox format
        is_valid, error = validator.validate_task_format("[_] Buy groceries")
        assert is_valid is False
        assert "must start with" in error
        
        # Empty task
        is_valid, error = validator.validate_task_format("[ ] ")
        assert is_valid is False
        assert "cannot be empty" in error
        
        # Invalid content in task
        is_valid, error = validator.validate_task_format("[ ] Task\nwith newline")
        assert is_valid is False
        assert "cannot contain" in error
    
    def test_clean_task_content(self, validator):
        # Basic cleaning
        assert validator.clean_task_content("  Buy groceries  ") == "Buy groceries"
        assert validator.clean_task_content("") == ""
        assert validator.clean_task_content("   ") == ""
        
        # Multiple spaces
        assert validator.clean_task_content("Buy    groceries") == "Buy groceries"
        assert validator.clean_task_content("  Multiple   spaces   here  ") == "Multiple spaces here"
    
    def test_is_actionable_task(self, validator):
        # Actionable tasks
        assert validator.is_actionable_task("Buy groceries") is True
        assert validator.is_actionable_task("Call mom") is True
        assert validator.is_actionable_task("Read the book") is True
        assert validator.is_actionable_task("Finish the report") is True
        assert validator.is_actionable_task("Schedule meeting") is True
        
        # Non-actionable tasks
        assert validator.is_actionable_task("note: remember this") is False
        assert validator.is_actionable_task("idea: new feature") is False
        assert validator.is_actionable_task("thought: about life") is False
        assert validator.is_actionable_task("reminder: birthday") is False
        assert validator.is_actionable_task("todo: something") is False
        assert validator.is_actionable_task("") is False
        assert validator.is_actionable_task("   ") is False
        
        # Edge cases
        assert validator.is_actionable_task("maybe buy groceries") is False  # Action word not in first 3
        assert validator.is_actionable_task("think about buying") is False
    
    def test_validate_and_clean_task_valid(self, validator):
        # Valid task
        cleaned, error = validator.validate_and_clean_task("  Buy groceries  ")
        assert cleaned == "Buy groceries"
        assert error is None
        
        # Valid actionable task
        cleaned, error = validator.validate_and_clean_task("Call mom", require_actionable=True)
        assert cleaned == "Call mom"
        assert error is None
    
    def test_validate_and_clean_task_invalid(self, validator):
        # Empty task
        cleaned, error = validator.validate_and_clean_task("")
        assert cleaned is None
        assert "cannot be empty" in error
        
        # Non-actionable task when required
        cleaned, error = validator.validate_and_clean_task("note: remember this", require_actionable=True)
        assert cleaned is None
        assert "must be actionable" in error
    
    def test_validate_task_file_line_valid(self, validator):
        # Valid task line
        is_valid, task, error = validator.validate_task_file_line("[ ] Buy groceries")
        assert is_valid is True
        assert task is not None
        assert task.content == "Buy groceries"
        assert task.completed is False
        assert error is None
        
        # Valid complete task line
        is_valid, task, error = validator.validate_task_file_line("[x] Read book")
        assert is_valid is True
        assert task is not None
        assert task.content == "Read book"
        assert task.completed is True
        assert error is None
        
        # Empty line
        is_valid, task, error = validator.validate_task_file_line("")
        assert is_valid is True
        assert task is None
        assert error is None
        
        # Whitespace only line
        is_valid, task, error = validator.validate_task_file_line("   ")
        assert is_valid is True
        assert task is None
        assert error is None
    
    def test_validate_task_file_line_invalid(self, validator):
        # Invalid format
        is_valid, task, error = validator.validate_task_file_line("Buy groceries")
        assert is_valid is False
        assert task is None
        assert "must start with" in error
        
        # Invalid content
        is_valid, task, error = validator.validate_task_file_line("[ ] Task\nwith newline")
        assert is_valid is False
        assert task is None
        assert "cannot contain" in error
        
        # Empty task
        is_valid, task, error = validator.validate_task_file_line("[ ] ")
        assert is_valid is False
        assert task is None
        assert "cannot be empty" in error