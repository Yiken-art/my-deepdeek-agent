
import sys
sys.path.insert(0, '.')

print("测试导入模块...")
from agent.llm_client import LLMClient
from agent.react_agent import ReActAgent
from tools import CalculatorTool, FileTool, ShellTool, GrepTool, GitTool
print("✅ 所有模块导入成功")

print("\n测试工具初始化...")
tools = [
    CalculatorTool(),
    FileTool(),
    ShellTool(),
    GrepTool(),
    GitTool()
]
print(f"✅ 工具初始化成功，共{len(tools)}个工具：{[t.name for t in tools]}")

print("\n测试LLM初始化...")
llm = LLMClient()
print("✅ LLM初始化成功")

print("\n测试Agent初始化...")
agent = ReActAgent(llm=llm, tools=tools, verbose=False)
print("✅ Agent初始化成功")

print("\n🎉 所有初始化测试通过！可以运行python main.py启动程序")
