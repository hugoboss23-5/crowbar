"""
Tool execution for Marcos.

Handles the actual execution of tools that Claude requests:
- bash: Execute shell commands
- read_file: Read file contents
- write_file: Write content to files
"""

import subprocess
import os
from pathlib import Path


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result as a string.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Dictionary of tool parameters

    Returns:
        String result of tool execution
    """

    if tool_name == "bash":
        return _execute_bash(tool_input)
    elif tool_name == "read_file":
        return _execute_read_file(tool_input)
    elif tool_name == "write_file":
        return _execute_write_file(tool_input)
    else:
        return f"ERROR: Unknown tool '{tool_name}'"


def _execute_bash(tool_input: dict) -> str:
    """Execute a bash command."""
    command = tool_input.get("command", "")
    if not command:
        return "ERROR: No command provided"

    try:
        # Get working directory from environment or use current
        working_dir = os.environ.get("MARCOS_WORKING_DIR", os.getcwd())

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=working_dir
        )

        output_parts = []

        if result.stdout:
            output_parts.append(result.stdout)

        if result.stderr:
            output_parts.append(f"STDERR: {result.stderr}")

        if result.returncode != 0:
            output_parts.append(f"Return code: {result.returncode}")

        return "\n".join(output_parts) if output_parts else "(no output)"

    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 30 seconds"
    except Exception as e:
        return f"ERROR: {str(e)}"


def _execute_read_file(tool_input: dict) -> str:
    """Read contents of a file."""
    path = tool_input.get("path", "")
    if not path:
        return "ERROR: No path provided"

    try:
        file_path = Path(path)

        if not file_path.exists():
            return f"ERROR: File not found: {path}"

        if not file_path.is_file():
            return f"ERROR: Path is not a file: {path}"

        # Check file size - don't read huge files
        size = file_path.stat().st_size
        if size > 1_000_000:  # 1MB limit
            return f"ERROR: File too large ({size} bytes). Maximum is 1MB."

        return file_path.read_text()

    except PermissionError:
        return f"ERROR: Permission denied reading: {path}"
    except UnicodeDecodeError:
        return f"ERROR: Cannot read binary file as text: {path}"
    except Exception as e:
        return f"ERROR reading file: {str(e)}"


def _execute_write_file(tool_input: dict) -> str:
    """Write content to a file."""
    path = tool_input.get("path", "")
    content = tool_input.get("content", "")

    if not path:
        return "ERROR: No path provided"

    try:
        file_path = Path(path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content)

        return f"Successfully wrote {len(content)} bytes to {path}"

    except PermissionError:
        return f"ERROR: Permission denied writing to: {path}"
    except Exception as e:
        return f"ERROR writing file: {str(e)}"
