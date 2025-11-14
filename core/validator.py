import re
from typing import List, Optional, Tuple
from .models import Task


class ValidationError(Exception):
    pass


class TaskValidator:
    def __init__(self):
        self.min_task_length = 1
        self.max_task_length = 500
        self.forbidden_chars = ['\n', '\r', '\t']
    
    def validate_task_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """Validate task content and return (is_valid, error_message)"""
        if not content or not content.strip():
            return False, "Task content cannot be empty"
        
        content = content.strip()
        
        # Length validation
        if len(content) < self.min_task_length:
            return False, f"Task content must be at least {self.min_task_length} character long"
        
        if len(content) > self.max_task_length:
            return False, f"Task content cannot exceed {self.max_task_length} characters"
        
        # Forbidden characters
        for char in self.forbidden_chars:
            if char in content:
                return False, f"Task content cannot contain {repr(char)}"
        
        # Only whitespace check
        if content.isspace():
            return False, "Task content cannot contain only whitespace"
        
        return True, None
    
    def validate_task_format(self, line: str) -> Tuple[bool, Optional[str]]:
        """Validate markdown task format and return (is_valid, error_message)"""
        if not line or not line.strip():
            return False, "Task line cannot be empty"
        
        line = line.strip()
        
        # Check for valid markdown checkbox format
        if not (line.startswith("[ ] ") or line.startswith("[x] ")):
            return False, "Task must start with '[ ] ' for incomplete or '[x] ' for complete"
        
        # Extract content after checkbox
        content = line[3:].strip()
        
        # Validate the content part
        is_valid, error = self.validate_task_content(content)
        if not is_valid:
            return False, error
        
        return True, None
    
    def clean_task_content(self, content: str) -> str:
        """Clean and normalize task content"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = content.strip()
        
        # Replace multiple spaces with single space
        content = re.sub(r'\s+', ' ', content)
        
        return content
    
    def is_actionable_task(self, content: str) -> bool:
        """Check if content represents an actionable task"""
        if not content or not content.strip():
            return False
        
        content = content.strip().lower()
        
        # Non-actionable patterns
        non_actionable_patterns = [
            r'^note[:\s]',
            r'^idea[:\s]',
            r'^thought[:\s]',
            r'^remember[:\s]',
            r'^reminder[:\s]',
            r'^todo[:\s]',
            r'^\s*$',
        ]
        
        for pattern in non_actionable_patterns:
            if re.match(pattern, content):
                return False
        
        # Check for action verbs (basic heuristic)
        action_indicators = [
            'buy', 'call', 'email', 'write', 'read', 'finish', 'start', 'complete',
            'schedule', 'book', 'order', 'pay', 'submit', 'send', 'create', 'update',
            'fix', 'repair', 'install', 'setup', 'configure', 'learn', 'research',
            'find', 'search', 'look', 'check', 'review', 'test', 'deploy', 'push',
            'pull', 'merge', 'branch', 'commit', 'build', 'run', 'execute', 'implement',
            'design', 'plan', 'organize', 'clean', 'wash', 'cook', 'prepare', 'pack',
            'go', 'visit', 'meet', 'attend', 'register', 'apply', 'sign', 'fill'
        ]
        
        words = content.split()
        return any(word in action_indicators for word in words[:3])  # Check first 3 words
    
    def validate_and_clean_task(self, content: str, require_actionable: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate and clean task content.
        Returns (cleaned_content, error_message)
        """
        # Clean the content first
        cleaned_content = self.clean_task_content(content)
        
        # Validate the cleaned content
        is_valid, error = self.validate_task_content(cleaned_content)
        if not is_valid:
            return None, error
        
        # Check if actionable if required
        if require_actionable and not self.is_actionable_task(cleaned_content):
            return None, "Task must be actionable (contain action verb)"
        
        return cleaned_content, None
    
    def validate_task_file_line(self, line: str) -> Tuple[bool, Optional[Task], Optional[str]]:
        """
        Validate a line from task file.
        Returns (is_valid, task_object, error_message)
        """
        if not line or not line.strip():
            return True, None, None  # Empty lines are valid
        
        line = line.strip()
        
        # Validate format
        is_valid, error = self.validate_task_format(line)
        if not is_valid:
            return False, None, error
        
        # Create task object
        try:
            task = Task.from_markdown(line)
            if task is None:
                return False, None, "Failed to parse task from markdown"
            return True, task, None
        except Exception as e:
            return False, None, f"Error parsing task: {str(e)}"
