"""
File Tools - Sandboxed File Operations
Provides secure file read/write operations restricted to the sandbox directory.
"""

import os
from pathlib import Path
from typing import Optional
import shutil


class FileTools:
    """
    Secure file operations with sandbox restrictions.
    All write operations are restricted to the sandbox directory.
    """
    
    def __init__(self, sandbox_dir: str = "sandbox"):
        """
        Initialize file tools with a sandbox directory.
        
        Args:
            sandbox_dir: Path to the sandbox directory
        """
        self.sandbox_dir = Path(sandbox_dir).resolve()
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        print(f"[FILE] File tools initialized with sandbox: {self.sandbox_dir}")
    
    def _is_safe_path(self, path: Path) -> bool:
        """
        Check if a path is within the sandbox.
        Prevents path traversal attacks.
        
        Args:
            path: Path to check
        
        Returns:
            True if path is safe, False otherwise
        """
        try:
            resolved = path.resolve()
            return resolved.is_relative_to(self.sandbox_dir)
        except (ValueError, RuntimeError):
            return False
    
    def read_file(self, file_path: str) -> str:
        """
        Read a file's content.
        Can read from anywhere (for input files).
        
        Args:
            file_path: Path to the file
        
        Returns:
            File content as string
        
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"[FILE] Read file: {path.name} ({len(content)} chars)")
            return content
        except Exception as e:
            raise IOError(f"Failed to read {file_path}: {e}")
    
    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file (SANDBOX ONLY).
        
        Args:
            file_path: Path to write to (must be in sandbox)
            content: Content to write
        
        Returns:
            True if successful
        
        Raises:
            PermissionError: If path is outside sandbox
            IOError: If write fails
        """
        path = Path(file_path)
        
        # Security check
        if not self._is_safe_path(path):
            raise PermissionError(
                f"Write denied: {file_path} is outside sandbox {self.sandbox_dir}"
            )
        
        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[FILE] Wrote file: {path.name} ({len(content)} chars)")
            return True
        
        except Exception as e:
            raise IOError(f"Failed to write {file_path}: {e}")
    
    def copy_to_sandbox(self, source_path: str) -> str:
        """
        Copy a file into the sandbox for safe modification.
        
        Args:
            source_path: Path to source file
        
        Returns:
            Path to the copied file in sandbox
        
        Raises:
            FileNotFoundError: If source doesn't exist
        """
        source = Path(source_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Create destination path (preserve filename)
        dest = self.sandbox_dir / source.name
        
        # Copy file
        shutil.copy2(source, dest)
        print(f"[FILE] Copied to sandbox: {source.name}")
        
        return str(dest)
    
    def get_sandbox_path(self, filename: str) -> str:
        """
        Get a path in the sandbox directory.
        
        Args:
            filename: Name of the file
        
        Returns:
            Full path in sandbox
        """
        return str(self.sandbox_dir / filename)
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file exists
        """
        return Path(file_path).exists()
    
    def clear_sandbox(self):
        """
        Clear all files from the sandbox.
        Use with caution!
        """
        for item in self.sandbox_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        print("[FILE] Sandbox cleared")