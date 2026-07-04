from .base_tool  import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "A tool for performing mathematical calculations."
    def run(self, query: str) -> str: 
        result = eval(query)
        return str(result)
