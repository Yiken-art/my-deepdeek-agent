
import os
from .base_tool import BaseTool

class GrepTool(BaseTool):
    name = "grep"
    description = """代码内容搜索工具，在指定目录下递归搜索包含指定关键字的文件，显示匹配的行号和内容。
输入格式：搜索关键字|目录路径（目录可选，默认当前目录）
示例：
def run|./tools
class ReActAgent|./agent
注意：会自动忽略venv、__pycache__、.git、node_modules等目录"""

    def run(self, input: str) -> str:
        try:
            parts = input.split("|", 1)
            keyword = parts[0].strip()
            if len(parts) > 1:
                search_dir = parts[1].strip()
            else:
                search_dir = "."
            
            if not keyword:
                return "错误：搜索关键字不能为空"
            
            if not os.path.isabs(search_dir):
                search_dir = os.path.abspath(search_dir)
            
            if not os.path.exists(search_dir):
                return f"错误：目录不存在 {search_dir}"
            
            # 忽略的目录
            ignore_dirs = {"venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode", "dist", "build"}
            matches = []
            
            for root, dirs, files in os.walk(search_dir):
                # 过滤忽略的目录
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                for file in files:
                    # 只搜索代码文件和文本文件
                    if not file.endswith(('.py', '.js', '.ts', '.java', '.go', '.c', '.cpp', '.h', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                if keyword in line:
                                    rel_path = os.path.relpath(file_path, search_dir)
                                    matches.append(f"{rel_path}:{i}: {line.strip()}")
                    except:
                        continue
            
            if not matches:
                return f"在 {search_dir} 下没有找到包含「{keyword}」的内容"
            
            # 最多返回20条匹配，防止结果太长
            if len(matches) > 20:
                result = f"找到 {len(matches)} 处匹配，显示前20条：\n"
                result += "\n".join(matches[:20])
            else:
                result = f"找到 {len(matches)} 处匹配：\n"
                result += "\n".join(matches)
            
            return result
        
        except Exception as e:
            return f"搜索失败：{str(e)}"
