
# DeepSeek 终端代码助手

一个轻量、本地运行的AI代码助手，基于DeepSeek大模型和ReAct框架，直接在终端帮你读代码、改bug、写功能、跑命令、提交Git。

对标Claude Code/OpenSeek，Python实现，零依赖，开箱即用。

## ✨ 功能特点

- 🚀 **本地运行**：所有代码都在你本地执行，数据不会上传到第三方
- ⚡ **流式输出**：思考过程实时打印，不用等半天才能看到结果
- 🔧 **完整工具链**：内置5个核心工具，覆盖90%日常开发场景：
  - 📄 文件操作：读文件、写文件、列目录，修改前自动显示diff预览
  - 💻 终端执行：运行任意Shell命令，自动超时保护，支持cd切换目录
  - 🔍 代码搜索：全局搜索代码内容，自动忽略无关目录
  - 📦 Git操作：查看状态、看diff、提交代码
  - 🧮 计算器：数学计算
- 🛡️ **安全保护**：
  - 危险操作（写文件、删文件、提交代码）执行前会让你确认
  - 修改文件前自动显示diff，清楚知道改了什么
  - 命令执行30秒超时，不会无限卡住
  - 读取文件限制大小，不会读大文件占满上下文
- 🧠 **智能上下文**：
  - 启动自动扫描项目结构，AI一开始就知道你项目有什么文件
  - 自动截断过长的对话历史，不会爆token
  - 修改代码强制先读再改，不会瞎覆盖
- 🎯 **专门优化DeepSeek**：提示词和工具调用格式专门为DeepSeek V4优化，调用成功率高
- 🎨 **友好终端界面**：彩色输出，verbose模式显示每一步思考过程，清楚知道AI在做什
- 
- 🛡️ **安全计算器**：AST语法树解析，只允许数学运算，防止代码注入
- 🩹 **错误自动修复**：命令/代码报错自动分析原因尝试修复，缺包自动装，语法错自动改，最多重试2次
- ⌨️ **命令历史**：支持上下键翻历史输入，自动保存1000条历史记录
- 📁 **文件工具增强**：支持创建文件夹，列目录自动忽略venv、__pycache__等无关文件
- 
么

## 📦 安装

1. 克隆项目
```bash
git clone <你的仓库地址>
cd my-agent
```

2. 安装依赖
```bash
pip install openai python-dotenv

# Windows用户如果需要命令历史功能，额外安装：
pip install pyreadline3


```

3. 配置API密钥
复制`.env.example`为`.env`，填写你的DeepSeek API密钥：
```env
LLM_API_KEY = "你的DeepSeek API Key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"
```

## 🚀 使用方法

直接运行主程序：
```bash
python main.py
```

启动后你就可以直接用自然语言下指令了，比如：

```
❯ 帮我看看这个项目的结构
❯ 列出tools目录下的所有文件
❯ 帮我读一下react_agent.py的run方法
❯ 运行python --version看看Python版本
❯ 搜索一下项目里哪里用到了BaseTool
❯ 帮我新建一个test.py，打印hello world
❯ 看看现在Git有什么修改
❯ 提交这次的代码，commit信息是feat: 新增核心工具
```

### 可用命令
- `/help`：显示帮助
- `/reset`：重置会话，清空对话历史
- `/exit`：退出程序

## 🏗️ 项目结构

```
my-agent/
├── agent/                     # Agent核心模块
│   ├── __init__.py
│   ├── llm_client.py          # 大模型客户端封装
│   └── react_agent.py         # ReAct思考框架核心实现
├── tools/                     # 工具模块
│   ├── __init__.py
│   ├── base_tool.py           # 工具抽象基类
│   ├── calculator.py          # 计算器工具
│   ├── file_tool.py           # 文件操作工具
│   ├── shell_tool.py          # 终端命令工具
│   ├── grep_tool.py           # 代码搜索工具
│   └── git_tool.py            # Git操作工具
├── main.py                    # CLI入口
├── .env                       # 配置文件（自己创建）
├── .env.example               # 配置示例
└── README.md                  # 说明文档
```

## 🧩 扩展工具

你可以很方便地扩展自己的工具，只需要继承`BaseTool`，实现三个属性即可：

```python
from tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"  # 工具名
    description = "工具描述，告诉AI这个工具能做什么"
    
    def run(self, input: str) -> str:
        # 工具逻辑，接收字符串输入，返回字符串结果
        return "工具执行结果"
```

然后在`main.py`里把你的工具加到tools列表里就行。

## 🛡️ 安全说明

- 所有危险操作（写文件、删除命令、Git提交）执行前都会询问你确认，不会自动执行
- 命令执行有30秒超时，不会无限卡住
- 读取文件限制最大100KB，不会读大文件占满上下文
- 所有操作都在本地执行，你的代码不会上传到任何地方，只有调用大模型的时候会发送必要的上下文

## 📝 开发计划

- [ ] 支持流式输出，AI回复实时打印
- [ ] 支持代码diff预览，修改文件前显示改动
- [ ] 项目记忆，自动记住项目结构和常用命令
- [ ] 支持更多工具：网络搜索、浏览器操作
- [ ] 支持多轮对话上下文持久化
- [ ] 配置文件支持自定义工具开关

## 📄 开源协议

MIT License
