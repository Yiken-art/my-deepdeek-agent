browser_toolimport webbrowser
from base_tool import BaseTool

class BrowserTool(BaseTool):
    name = "browser"
    description = """浏览器工具，调用系统默认浏览器打开指定网页。
输入格式：open|网页地址
示例：
open|https://github.com
注意：会弹出系统默认浏览器窗口，仅支持打开网页"""

    def run(self, input: str) -> str:
        try:
            parts = input.split("|", 1)
            action = parts[0].strip()
            if action == "open":
                if len(parts) < 2:
                    return "错误：open操作需要指定网页地址，格式：open|https://xxx.com"
                url = parts[1].strip()
                webbrowser.open(url)
                return f"✅ 已在默认浏览器打开网页：{url}"
            else:
                return f"错误：不支持的操作 {action}，当前支持：open"
        except Exception as e:
            return f"浏览器操作失败：{str(e)}"
          
.py
