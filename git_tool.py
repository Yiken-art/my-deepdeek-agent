
import subprocess
import os
from .base_tool import BaseTool

class GitTool(BaseTool):
    name = "git"
    description = """Git版本控制工具，支持常用Git操作。
输入格式：操作类型[|参数]
支持的操作：
- status：查看工作区状态
- diff：查看未暂存的修改
- log：查看最近10条提交记录
- add|文件路径：添加文件到暂存区（.代表所有文件）
- commit|提交信息：提交暂存区的修改
示例：
status
diff
add|.
commit|feat: 新增文件操作工具
注意：提交代码前会先让你确认"""

    def run(self, input: str) -> str:
        try:
            parts = input.split("|", 1)
            action = parts[0].strip()
            param = parts[1].strip() if len(parts) > 1 else ""

            if action == "status":
                result = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=os.getcwd())
                return result.stdout + result.stderr

            elif action == "diff":
                result = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=os.getcwd())
                output = result.stdout + result.stderr
                if len(output) > 3000:
                    output = output[:3000] + "\n... diff过长，已截断"
                return output

            elif action == "log":
                result = subprocess.run(["git", "log", "--oneline", "-n", "10"], capture_output=True, text=True, cwd=os.getcwd())
                return result.stdout + result.stderr

            elif action == "add":
                if not param:
                    return "错误：add操作需要指定文件路径，.代表所有文件"
                result = subprocess.run(["git", "add", param], capture_output=True, text=True, cwd=os.getcwd())
                return result.stdout + result.stderr if result.returncode == 0 else f"add失败：{result.stderr}"

            elif action == "commit":
                if not param:
                    return "错误：commit操作需要提交信息"
                result = subprocess.run(["git", "commit", "-m", param], capture_output=True, text=True, cwd=os.getcwd())
                return result.stdout + result.stderr if result.returncode == 0 else f"commit失败：{result.stderr}"

            else:
                return f"错误：不支持的Git操作 {action}，支持的操作：status/diff/log/add/commit"

        except Exception as e:
            return f"Git操作失败：{str(e)}"
