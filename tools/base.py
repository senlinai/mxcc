import subprocess
import os

# 1.命令行执行工具
def run_bash(command):
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Command contains potentially dangerous operations."
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=120
        )
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"

# 2.阅读文件内容
def read_file(file_path):
    if not os.path.isfile(file_path):
        return "Error: File does not exist."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content[:50000] if content else "(empty file)"
    except Exception as e:
        return f"Error: {e}"

# 3.写入文件内容
def write_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return "File written successfully."
    except Exception as e:
        return f"Error: {e}"    
    
# 4.编辑文件内容
def edit_file(file_path, old_content, new_content):
    if not os.path.isfile(file_path):
        return "Error: File does not exist."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_content not in content:
            return "Error: Old content not found in file."
        updated_content = content.replace(old_content, new_content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return "File edited successfully."
    except Exception as e:
        return f"Error: {e}"

#################
BASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    }
                },
                "required": ["command"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit content in a file by replacing old content with new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "Content in the file that needs to be replaced"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content that will replace the old content in the file"
                    }
                },
                "required": ["file_path", "new_content"],
            }, 
        }
    }
]