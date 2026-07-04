
import sys
sys.path.insert(0, '.')

from agent.llm_client import LLMClient
from agent.react_agent import ReActAgent
from tools.calculator import CalculatorTool

def test_agent():
    print("="*60)
    print("初始化Agent...")
    llm = LLMClient()
    agent = ReActAgent(llm=llm, tools=[CalculatorTool()])
    print("✅ Agent初始化完成，已加载工具：", list(agent.tools.keys()))
    print("="*60)

    # 测试1：复杂乘法，模型自己算不对，必须调用工具
    print("\n🧪 测试1：复杂乘法计算（必须调用工具）")
    print("问题：123456 乘以 789012 等于多少？必须调用计算器工具计算")
    print("-"*60)
    try:
        result = agent.run("123456 乘以 789012 等于多少？必须调用计算器工具计算，不能自己算")
        print(f"\n✅ 最终答案：{result}")
        # 验证结果是否正确
        correct = 123456 * 789012
        print(f"🧮 正确结果：{correct}")
        if str(correct) in result:
            print("✅ 结果正确，工具调用成功！")
        else:
            print("❌ 结果错误，工具可能没被正确调用")
            
    except Exception as e:
        print(f"\n❌ 测试1出错：{str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    # 测试2：不需要工具的问题
    print("\n🧪 测试2：不需要工具的普通对话")
    print("问题：你好，用一句话介绍一下你自己")
    print("-"*60)
    try:
        agent2 = ReActAgent(llm=llm, tools=[CalculatorTool()])
        result = agent2.run("你好，用一句话介绍一下你自己")
        print(f"✅ 回答：{result}")
    except Exception as e:
        print(f"\n❌ 测试2出错：{str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_agent()
