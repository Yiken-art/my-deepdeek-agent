
# 测试导入是否正常，不调用API
import sys
sys.path.insert(0, '.')

print("测试导入LLMClient...")
from agent.llm_client import LLMClient
print("✅ LLMClient导入成功")

print("测试导入BaseTool...")
from tools.base_tool import BaseTool
print("✅ BaseTool导入成功")

print("测试导入CalculatorTool...")
from tools.calculator import CalculatorTool
print("✅ CalculatorTool导入成功")

print("测试导入ReActAgent...")
from agent.react_agent import ReActAgent
print("✅ ReActAgent导入成功")

print("\n测试初始化工具...")
calc = CalculatorTool()
print(f"✅ 计算器初始化成功，名称：{calc.name}")
print(f"✅ 计算器测试计算 1+2：{calc.run('1+2')}")

print("\n测试初始化Agent（不调用LLM）...")
llm = LLMClient()
agent = ReActAgent(llm=llm, tools=[calc])
print(f"✅ Agent初始化成功，已加载工具：{list(agent.tools.keys())}")
print(f"✅ 历史消息数量：{len(agent.history)}（包含系统提示词）")

print("\n🎉 所有导入和初始化测试通过！代码没有语法和导入错误")
