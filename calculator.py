from .base_tool import BaseTool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "用于执行数学算术表达式计算，输入为合法的数学表达式字符串，返回计算结果"
    def run(self, input: str) -> str:
        try:
            # 正常执行的代码：计算表达式并返回字符串结果
            result = eval(input)
            return str(result)
        except Exception as e:
            # 出错时执行：返回错误提示
            return f"计算失败：{str(e)}"