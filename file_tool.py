import os
import os
from .base_tool import BaseTool

class FileTool(BaseTool):
    name = "file"
    description = """文件操作工具，支持读取文件、写入文件、列出目录内容。
输入格式：
- 读取文件：read|文件路径
- 写入文件：write|文件路径|内容
- 列出目录：ls|目录路径
示例：
read|./agent/react_agent.py
write|./test.txt|hello world
ls|./tools
注意：路径使用相对路径，相对于当前项目根目录。"""

    def run(self, input: str) -> str:
        try:
            parts = input.split("|", 2)
            if len(parts) < 2:
                return "格式错误，请使用：操作类型|路径[|内容]"
            
            action = parts[0].strip()
            path = parts[1].strip()
            
            # 处理相对路径，基于当前工作目录
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            if action == "read":
                if not os.path.exists(path):
                    return f"错误：文件不存在 {path}"
                if os.path.isdir(path):
                    return f"错误：{path} 是目录，不是文件，请使用ls操作"
                # 限制读取文件大小，最大100KB，防止读大文件占满上下文
                if os.path.getsize(path) > 100 * 1024:
                    return f"错误：文件过大（{os.path.getsize(path)/1024:.1f}KB），请读取更小的文件或分段读取"
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return f"文件 {path} 内容：\n{content}"
            
            elif action == "write":
                if len(parts) < 3:
                    return "格式错误，写入文件需要：write|路径|内容"
                content = parts[2]
                # 自动创建父目录
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"成功写入文件 {path}，共{len(content)}字符"
            
            elif action == "ls":
                if not os.path.exists(path):
                    return f"错误：目录不存在 {path}"
                if not os.path.isdir(path):
                    return f"错误：{path} 是文件，不是目录"
                files = os.listdir(path)
                result = [f"目录 {path} 下的内容："]
                for f in files:
                    full_path = os.path.join(path, f)
                    if os.path.isdir(full_path):
                        result.append(f"  📁 {f}/")
                    else:
                        size = os.path.getsize(full_path)
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024*1024:
                            size_str = f"{size/1024:.1f}KB"
                        else:
                            size_str = f"{size/1024/1024:.1f}MB"
                        result.append(f"  📄 {f} ({size_str})")
                return "\n".join(result)
            
            else:
                return f"错误：不支持的操作 {action}，支持的操作：read/write/ls"
        
        except Exception as e:
            return f"文件操作失败：{str(e)}"
