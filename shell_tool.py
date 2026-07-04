
import subprocess
import os
from .base_tool import BaseTool

class ShellTool(BaseTool):
    name = "shell"
    description = """执行终端Shell命令，返回命令输出结果。支持cd切换目录，会记住当前工作目录。
输入格式：直接输入要执行的命令即可
示例：
python --version
pip list
dir
cd tools
dir
注意：
1. Windows系统使用PowerShell/CMD命令，Linux/macOS使用bash命令
2. 命令执行超时时间为30秒，超时会自动终止
3. 危险命令（如删除文件、格式化磁盘）会在执行前询问你确认
4. 一次只执行一条命令
5. 支持cd命令切换目录，切换后后续命令都会在新目录执行"""

    def __init__(self):
        # 维护当前工作目录
        self.cwd = os.getcwd()

    def run(self, input: str) -> str:
        try:
            cmd = input.strip()
            if not cmd:
                return "错误：命令不能为空"

            # 处理cd命令，自己维护工作目录，不通过subprocess执行（因为subprocess cd不生效）
            if cmd.startswith("cd "):
                path = cmd[3:].strip()
                # 处理~
                if path.startswith("~"):
                    path = os.path.expanduser(path)
                # 处理相对路径
                if not os.path.isabs(path):
                    path = os.path.join(self.cwd, path)
                # 规范化路径
                path = os.path.normpath(path)
                if os.path.exists(path) and os.path.isdir(path):
                    self.cwd = path
                    return f"已切换到目录：{self.cwd}"
                else:
                    return f"错误：目录不存在 {path}"

            # 检测危险命令
            dangerous_keywords = ["rm -rf", "del /f", "format", "mkfs", "dd if=", ":(){ :|:& };:"]
            for kw in dangerous_keywords:
                if kw in cmd.lower():
                    return f"⚠️ 检测到危险命令：{cmd}，请确认你真的要执行这个命令，确认后再重新执行"

            # 执行命令，超时30秒，用维护的cwd
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.cwd
            )

            output = ""
            if result.stdout:
                output += f"标准输出：\n{result.stdout}\n"
            if result.stderr:
                output += f"错误输出：\n{result.stderr}\n"
            output += f"退出码：{result.returncode}\n当前目录：{self.cwd}"

            # 限制输出长度，最大2000字符，防止输出太长占满上下文
            if len(output) > 2000:
                output = output[:2000] + "\n... 输出过长，已截断"

            return output

        except subprocess.TimeoutExpired:
            return "错误：命令执行超时（超过30秒），已自动终止"
        except Exception as e:
            return f"命令执行失败：{str(e)}"
