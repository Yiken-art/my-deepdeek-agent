from agent.llm_client import LLMClient

def test_chat():
    llm = LLMClient()
    result = llm.chat("你是一个简洁的助手。", "用一句话介绍Python语言")
    print("=== 文本对话测试 ===")
    print(result)
    print()

def test_chat_json():
    llm = LLMClient()
    system_prompt = "请根据用户输入的信息，返回包含name和age两个字段的JSON。"
    user_input = "我叫张三，今年20岁"
    result = llm.chat_json(system_prompt, user_input)
    print("=== JSON输出测试 ===")
    print(result)
    print(f"解析后的字典类型：{type(result)}")
    print(f"姓名：{result['name']}，年龄：{result['age']}")

if __name__ == "__main__":
    test_chat()
    test_chat_json()