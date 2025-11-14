from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime


class Timeframe(Enum):
    VOMIT = "_1_vomit.txt"
    TODAY = "_2_today.md"
    WEEK = "_3_week.md"
    MONTH = "_4_month.md"
    YEAR = "_5_year.md"


@dataclass
class Task:
    content: str
    completed: bool = False
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_markdown(self) -> str:
        checkbox = "[x]" if self.completed else "[ ]"
        return f"{checkbox} {self.content}"
    
    @classmethod
    def from_markdown(cls, line: str) -> Optional['Task']:
        line = line.strip()
        if not line:
            return None
        
        if line.startswith("[x] "):
            content = line[3:].strip()
            return cls(content=content, completed=True)
        elif line.startswith("[ ] "):
            content = line[3:].strip()
            return cls(content=content, completed=False)
        else:
            return None


@dataclass
class TaskFile:
    timeframe: Timeframe
    tasks: List[Task]
    
    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
    
    def remove_task(self, task_content: str) -> bool:
        for i, task in enumerate(self.tasks):
            if task.content == task_content:
                self.tasks.pop(i)
                return True
        return False
    
    def find_tasks(self, pattern: str) -> List[Task]:
        pattern_lower = pattern.lower()
        return [task for task in self.tasks if pattern_lower in task.content.lower()]
    
    def get_completed_count(self) -> int:
        return sum(1 for task in self.tasks if task.completed)
    
    def get_total_count(self) -> int:
        return len(self.tasks)