import os
from pathlib import Path
from typing import Optional
from .models import TaskFile, Task, Timeframe


class FileOperations:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path.cwd()
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
    
    def get_file_path(self, timeframe: Timeframe) -> Path:
        return self.data_dir / timeframe.value
    
    def read_task_file(self, timeframe: Timeframe) -> TaskFile:
        file_path = self.get_file_path(timeframe)
        tasks = []
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    task = Task.from_markdown(line)
                    if task:
                        tasks.append(task)
        
        return TaskFile(timeframe=timeframe, tasks=tasks)
    
    def write_task_file(self, task_file: TaskFile) -> None:
        file_path = self.get_file_path(task_file.timeframe)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for task in task_file.tasks:
                f.write(task.to_markdown() + '\n')
    
    def append_to_file(self, timeframe: Timeframe, content: str) -> None:
        file_path = self.get_file_path(timeframe)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
    
    def clear_file(self, timeframe: Timeframe) -> None:
        file_path = self.get_file_path(timeframe)
        
        if file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')
    
    def file_exists(self, timeframe: Timeframe) -> bool:
        return self.get_file_path(timeframe).exists()
    
    def create_file_if_not_exists(self, timeframe: Timeframe) -> None:
        file_path = self.get_file_path(timeframe)
        
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
    
    def backup_file(self, timeframe: Timeframe, backup_suffix: str = ".backup") -> bool:
        file_path = self.get_file_path(timeframe)
        
        if not file_path.exists():
            return False
        
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return True
        except Exception:
            return False