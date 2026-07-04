
import sys
sys.path.insert(0, '.')

from agent.llm_client import LLMClient
from agent.react_agent import ReActAgent
from tools.calculator import CalculatorTool

def test_verbose():
    print("="*60)
    print("Verbose模式测试，打印每一步过程")
    print("="*60)
    
    llm = LLMClient()
    agent = ReActAgent(llm=llm, tools=[CalculatorTool()])
    
    query = "2的20次方等于多少？必须调用计算器计算"
    print(f"\n用户问题：{query}")
    print("-"*60)
    
    agent.history.append({"role": "user", "content": query})
    max_steps = 5
    tool_called = False
    
    for step in range(max_steps):
        print(f"\n📝 第{step+1}轮：")
        response = agent.llm.chat(agent.history)
        print("模型输出：")
        print(response)
        agent.history.append({"role": "assistant", "content": response})
        
        if "行动：" in response:
            action_part = response.split("行动：")[-1].strip().split("\n")[0].strip()
            if "|" in action_part:
                tool_name, tool_args = action_part.split("|", 1)
                tool_name = tool_name.strip()
                tool_args = tool_args.strip()
            else:
                tool_name = action_part.strip()
                tool_args = ""
            
            print(f"\n🔧 调用工具：{tool_name}，参数：{tool_args}")
            tool_called = True
            
            if tool_name in agent.tools:
                tool_result = agent.tools[tool_name].run(tool_args)
                print(f"✅ 工具返回结果：{tool_result}")
                agent.history.append({"role": "user", "content": f"工具返回结果：{tool_result}"})
            else:
                print(f"❌ 工具不存在")
                agent.history.append({"role": "user", "content": f"错误：不存在名为 {tool_name} 的工具"})
                
        elif "答案：" in response:
            answer = response.split("答案：")[-1].strip()
            print(f"\n🎉 最终答案：{answer}")
            break
        else:
            print("\n⚠️ 格式错误，提示重新输出")
            agent.history.append({"role": "user", "content": "格式错误，请按要求输出"})
    
    print("\n" + "="*60)
    if tool_called:
        print("✅ 工具确实被调用了，ReAct流程正常！")
    else:
        print("❌ 工具没有被调用，模型跳步了")
    
    correct = 2**20
    print(f"🧮 正确结果：{correct}")

if __name__ == "__main__":
    test_verbose()
