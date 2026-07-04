
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm_client import LLMClient
from agent.react_agent import ReActAgent
from tools import (
    CalculatorTool,
    FileTool,
    ShellTool,
    GrepTool,
    GitTool
)

# 终端颜色
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    banner = f"""{Colors.BLUE}{Colors.BOLD}
╔═══════════════════════════════════════════════╗
║           DeepSeek 终端代码助手 v0.1          ║
║     本地运行 · 代码开发 · 文件操作 · Git       ║
╚═══════════════════════════════════════════════╝
{Colors.END}
可用命令：
  /help   显示帮助
  /reset  重置会话，清空历史
  /exit   退出程序
"""
    print(banner)

def main():
    print_banner()
    
    # 初始化LLM和Agent
    print(f"{Colors.YELLOW}🔄 正在初始化...{Colors.END}")
    try:
        llm = LLMClient()
        tools = [
            CalculatorTool(),
            FileTool(),
            ShellTool(),
            GrepTool(),
            GitTool()
        ]
        agent = ReActAgent(llm=llm, tools=tools, verbose=True)
        print(f"{Colors.GREEN}✅ 初始化完成，已加载工具：{[t.name for t in tools]}{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ 初始化失败：{str(e)}{Colors.END}")
        print("请检查.env文件中的API配置是否正确")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}💡 你可以直接输入问题，比如：{Colors.END}")
    print("  - 帮我看看这个项目的结构")
    print("  - 运行一下测试脚本")
    print("  - 帮我在tools目录下新建一个hello.py，打印hello world")
    print("  - 看看react_agent.py里的run方法是怎么实现的\n")
    
    while True:
        try:
            user_input = input(f"{Colors.BOLD}❯ {Colors.END}").strip()
            if not user_input:
                continue
            
            # 处理斜杠命令
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()
                if cmd == "exit" or cmd == "quit":
                    print(f"{Colors.YELLOW}👋 再见！{Colors.END}")
                    break
                elif cmd == "reset":
                    agent.reset()
                    print(f"{Colors.GREEN}✅ 会话已重置{Colors.END}")
                    continue
                elif cmd == "help":
                    print_banner()
                    continue
                else:
                    print(f"{Colors.RED}❌ 未知命令：{cmd}，输入/help查看帮助{Colors.END}")
                    continue
            
            # 运行Agent
            print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
            answer = agent.run(user_input)
            print(f"\n{Colors.GREEN}{Colors.BOLD}📝 最终回答：{Colors.END}")
            print(f"{Colors.GREEN}{answer}{Colors.END}")
            print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}👋 再见！{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}❌ 运行出错：{str(e)}{Colors.END}")

if __name__ == "__main__":
    main()
