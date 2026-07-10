import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import json

# 加载.env配置文件
load_dotenv()

class LLMClient:
    def __init__(self):
        # 从环境变量读取配置
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        
        # 初始化OpenAI客户端（兼容所有OpenAI格式的接口）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(self, system_prompt=None, user_message=None, messages=None, max_retries: int = 3) -> str:
        """
        基础文本对话，支持两种调用方式：
        1. 单轮对话：chat(system_prompt, user_message)
        2. 多轮对话：chat(messages=消息列表) 或 chat(消息列表)
        :param system_prompt: 系统提示词（单轮模式用）
        :param user_message: 用户输入（单轮模式用）
        :param messages: 完整消息列表（多轮模式用，优先级更高）
        :param max_retries: 最大重试次数
        :return: 模型返回的纯文本
        """
        # 兼容直接传messages列表作为第一个参数的调用方式
        if isinstance(system_prompt, list):
            messages = system_prompt
            system_prompt = None
            user_message = None

        # 构建最终要发送的消息列表
        if messages is not None:
            send_messages = messages
        else:
            if system_prompt is None or user_message is None:
                raise ValueError("单轮模式必须提供system_prompt和user_message，多轮模式必须提供messages")
            send_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

        retry_count = 0
        while retry_count < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=send_messages,
                    temperature=0.1  # Agent场景用低温，输出更稳定
                )
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"LLM调用失败，已重试{max_retries}次，错误：{str(e)}")
                # 指数退避重试，等待时间逐次增加
                wait_time = 2 ** retry_count
                time.sleep(wait_time)

    def chat_stream(self, messages: list, max_retries: int = 3):
        """
        流式对话，逐块返回模型输出
        :param messages: 完整消息列表
        :param max_retries: 最大重试次数
        :return: 生成器，逐块yield文本内容
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    stream=True
                )
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    yield f"\n[错误] LLM调用失败，已重试{max_retries}次，错误：{str(e)}"
                    return
                wait_time = 2 ** retry_count
                time.sleep(wait_time)

    def chat_with_history(self, messages: list) -> str:
        """直接接收完整的消息列表，调用大模型API（兼容旧代码）"""
        return self.chat(messages=messages)
      


