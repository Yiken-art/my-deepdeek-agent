from datetime import datetime
from .base_tool import BaseTool

class TimeTool(BaseTool):
    # 工具唯一名称，模型会输出这个名字来调用
    name = "get_current_time"
    # 工具功能描述，告诉模型什么时候该用它
    description = "用于获取当前的日期和时间，当用户询问现在几点、今天几号等时间相关问题时使用"

    def run(self, query: str) -> str:
        # 获取当前时间，格式化成人易懂的字符串
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        return f"当前时间是：{now}"