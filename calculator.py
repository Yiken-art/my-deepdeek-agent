import ast
import operator
from .base_tool import BaseTool

# 支持的运算符
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "用于执行数学算术表达式计算，支持加减乘除、取模、幂运算、括号，输入为合法的数学表达式字符串，返回计算结果。禁止执行非数学表达式。"
    
    def _eval_expr(self, node):
        """递归安全计算表达式"""
        if isinstance(node, ast.Constant):
            # 只允许数字
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量类型：{type(node.value)}")
        elif isinstance(node, ast.BinOp):
            # 二元运算
            op_type = type(node.op)
            if op_type not in ALLOWED_OPERATORS:
                raise ValueError(f"不支持的运算符：{op_type.__name__}")
            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            return ALLOWED_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            # 一元运算（负号、正号）
            op_type = type(node.op)
            if op_type not in ALLOWED_OPERATORS:
                raise ValueError(f"不支持的一元运算符：{op_type.__name__}")
            operand = self._eval_expr(node.operand)
            return ALLOWED_OPERATORS[op_type](operand)
        else:
            raise ValueError(f"不支持的表达式类型：{type(node).__name__}")

    def run(self, input: str) -> str:
        try:
            input = input.strip()
            # 解析表达式
            tree = ast.parse(input, mode='eval')
            result = self._eval_expr(tree.body)
            return str(result)
        except Exception as e:
            return f"计算失败：{str(e)}，请输入合法的数学表达式，例如：(2+3)*4/2"from .base_tool import BaseTool
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
