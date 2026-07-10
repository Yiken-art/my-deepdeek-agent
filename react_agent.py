import re
import difflib
from typing import List, Dict, Optional
import sys
import os
from llm_client import LLMClient
from base_tool import BaseTool


class ReActAgent:
    def __init__(self, llm: LLMClient, tools: List[BaseTool], verbose: bool = False):
        # 1. 注入大模型客户端（依赖注入，外部创建后传入）
        self.llm = llm
        self.verbose = verbose  # 是否打印详细过程

        # 2. 工具列表转「名称→对象」字典，O(1) 快速查找
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

        # 3. 初始化对话历史列表，存储所有轮次的消息
        self.history: List[dict] = []
        
        # 错误重试计数，最多自动修复2次
        self.error_retry_count = 0

        # 4. 构建系统提示词并加入对话历史
        self._init_system_prompt()

    def _scan_project_structure(self, root_path: str, max_depth: int = 3) -> str:
        """扫描项目结构，生成目录树"""
        ignore_dirs = {"venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode", "dist", "build", ".egg-info"}
        result = []
        
        def _scan(path, depth, prefix=""):
            if depth > max_depth:
                return
            try:
                items = sorted(os.listdir(path))
            except:
                return
            # 过滤忽略的目录
            items = [i for i in items if i not in ignore_dirs and not i.startswith(".")]
            for i, item in enumerate(items):
                full_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                result.append(f"{prefix}{current_prefix}{item}{'/' if os.path.isdir(full_path) else ''}")
                if os.path.isdir(full_path):
                    extension = "    " if is_last else "│   "
                    _scan(full_path, depth + 1, prefix + extension)
        
        result.append(os.path.basename(root_path) + "/")
        _scan(root_path, 1)
        return "\n".join(result)

    def _init_system_prompt(self):
        """私有方法：动态生成系统提示词，包含所有工具信息与思考规则"""
        # 拼接所有工具的名称与描述
        tool_info_list = []
        for tool in self.tools.values():
            tool_info_list.append(f"- {tool.name}：{tool.description}")
        tool_info_str = "\n".join(tool_info_list)

        # 扫描项目结构
        project_structure = self._scan_project_structure(os.getcwd())

        system_prompt = f"""你是一个专业的终端代码助手，运行在用户的本地电脑上，帮助用户完成代码开发、调试、文件操作、命令执行等任务。你必须严格按照ReAct思考框架执行，绝对禁止跳步。

当前工作目录：{os.getcwd()}

当前项目结构：
{project_structure}

可用工具列表：
{tool_info_str}

🔴 绝对禁止的行为：
1. 禁止在同一次回复中同时出现「行动：」和「答案：」
2. 禁止提前想象、猜测工具返回结果，必须等工具返回真实结果后再继续思考
3. 禁止跳过工具调用，自己编造结果，所有文件操作、命令执行、代码搜索都必须调用工具完成
4. 每次回复只能有一个「思考：」段落，思考后只能二选一：要么调用工具，要么给出答案
5. 不要输出多余的解释，严格按照格式输出
6. 修改代码前必须先读取原文件内容，绝对禁止在不知道原内容的情况下直接写文件覆盖
7. 修改代码尽量做最小改动，不要重构整个文件，只改需要改的部分
8. 写文件时注意使用UTF-8编码，Python文件要注意缩进正确
9. 同一个错误最多尝试修复2次，修复不了就告诉用户问题在哪，不要无限循环重试

🩹 错误自动修复规则：
1. 如果执行命令报错（比如Python语法错误、缺少依赖包、命令不存在），不要直接把错误返回给用户
2. 先分析错误原因，尝试自己修复：
   - 缺包就执行pip install安装对应依赖
   - 代码语法错误就读取文件，修改错误后重新运行
   - 命令不存在就换正确的命令
3. 最多尝试修复2次，如果还是失败，再告诉用户具体错误和解决方法

🟢 正确执行流程：
1. 第一步：思考问题，判断需要调用什么工具，只输出「思考：...」+「行动：工具名|参数」
2. 等待工具返回真实结果
3. 第二步：基于工具返回的真实结果继续思考，如果信息足够就输出答案，不够就继续调用工具
4. 修改文件时：先读原文件→思考修改方案→写文件，绝对不能跳过读文件直接写
5. 信息充足后，输出「思考：我已经获得足够信息，可以给出答案」+「答案：最终内容」

📝 严格输出格式：
需要调用工具时：
思考：你对当前问题的分析和下一步计划
行动：工具名称|参数内容

不需要调用工具/信息足够时：
思考：我已经获得足够信息，可以给出答案
答案：你的最终回答内容
"""

        # 系统消息加入对话历史开头
        self.history.append({"role": "system", "content": system_prompt})

    def _truncate_history(self):
        """上下文自动截断，防止历史太长超过token限制"""
        # 保留系统提示词，最多保留最近20条消息
        if len(self.history) > 21:  # 1条系统提示词 + 20条消息
            self.history = [self.history[0]] + self.history[-20:]

    def _confirm_dangerous_action(self, tool_name: str, input_text: str) -> bool:
        """危险操作确认，返回True表示允许执行，False表示取消"""
        dangerous = False
        reason = ""
        diff_text = ""
        
        # 写文件操作，显示diff
        if tool_name == "file" and input_text.startswith("write|"):
            dangerous = True
            parts = input_text.split("|", 2)
            if len(parts) >= 3:
                file_path = parts[1].strip()
                new_content = parts[2]
                # 处理相对路径
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                reason = f"写入/修改文件：{file_path}"
                # 如果文件存在，生成diff
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            old_content = f.read()
                        # 生成统一diff
                        diff_lines = list(difflib.unified_diff(
                            old_content.splitlines(keepends=True),
                            new_content.splitlines(keepends=True),
                            fromfile=f"a/{os.path.basename(file_path)}",
                            tofile=f"b/{os.path.basename(file_path)}"
                        ))
                        # 给diff加颜色
                        colored_diff = []
                        for line in diff_lines:
                            if line.startswith('+') and not line.startswith('+++'):
                                colored_diff.append(f"\033[92m{line}\033[0m")  # 新增行绿色
                            elif line.startswith('-') and not line.startswith('---'):
                                colored_diff.append(f"\033[91m{line}\033[0m")  # 删除行红色
                            elif line.startswith('@@'):
                                colored_diff.append(f"\033[96m{line}\033[0m")  # 位置标记青色
                            else:
                                colored_diff.append(line)
                        diff_text = "\n变更内容：\n" + "".join(colored_diff)
                    except Exception as e:
                        diff_text = f"\n无法读取原文件生成diff：{str(e)}"
                else:
                    diff_text = f"\n新文件，将创建：{file_path}"
        # 删除类命令
        elif tool_name == "shell":
            dangerous_keywords = ["rm ", "del ", "format", "mkfs", "dd ", "rmdir", "rd "]
            for kw in dangerous_keywords:
                if kw in input_text.lower():
                    dangerous = True
                    reason = f"执行可能删除数据的命令：{input_text}"
                    break
        # Git提交操作
        elif tool_name == "git" and input_text.startswith("commit|"):
            dangerous = True
            commit_msg = input_text.split("|", 1)[1].strip() if "|" in input_text else ""
            reason = f"提交Git代码：{commit_msg}"
        
        if dangerous:
            print(f"\n⚠️  即将执行危险操作：{reason}")
            if diff_text:
                print(diff_text)
            confirm = input("是否确认执行？(y/N): ").strip().lower()
            return confirm == "y"
        return True

    def reset(self):
        """重置对话历史，开始新的会话"""
        self.history = [self.history[0]]  # 保留系统提示词
        self.error_retry_count = 0  # 重置错误重试计数

    def run(self, query: str) -> str:
        # 将用户问题加入对话历史
        self.history.append({"role": "user", "content": query})
        max_steps = 10  # 最大思考步数，防止模型无限循环

        for step in range(max_steps):
            # 自动截断过长的历史
            self._truncate_history()

            if self.verbose:
                print(f"\n🤔 第{step+1}步思考中...")
                print("模型输出：")

            # 1. 流式调用大模型，实时打印输出
            response = ""
            for chunk in self.llm.chat_stream(self.history):
                response += chunk
                if self.verbose:
                    print(chunk, end="", flush=True)
            response = response.strip()
            self.history.append({"role": "assistant", "content": response})

            if self.verbose:
                print("\n" + "-"*50)

            # 2. 优先判断是否需要调用工具（必须先判断行动，防止跳步）
            if "行动：" in response:
                action_part = response.split("行动：")[-1].strip().split("\n")[0].strip()
                if "|" in action_part:
                    tool_name, tool_args = action_part.split("|", 1)
                    tool_name = tool_name.strip()
                    tool_args = tool_args.strip()
                else:
                    tool_name = action_part.strip()
                    tool_args = ""

                if self.verbose:
                    print(f"🔧 调用工具：{tool_name}，参数：{tool_args}")

                # 危险操作确认
                if not self._confirm_dangerous_action(tool_name, tool_args):
                    self.history.append({
                        "role": "user",
                        "content": "操作已被用户取消，请根据用户的指示调整"
                    })
                    continue

                if tool_name in self.tools:
                    try:
                        # 执行工具
                        tool_result = self.tools[tool_name].run(tool_args)
                        # 执行成功，重置错误计数
                        self.error_retry_count = 0
                        if self.verbose:
                            print(f"✅ 工具返回：{tool_result[:200]}..." if len(tool_result) > 200 else f"✅ 工具返回：{tool_result}")
                            print("-"*50)
                        # 将结果加入历史，进入下一轮思考
                        self.history.append({
                            "role": "user",
                            "content": f"工具返回结果：{tool_result}"
                        })
                    except Exception as e:
                        self.error_retry_count += 1
                        if self.error_retry_count >= 2:
                            # 超过2次重试，直接返回错误
                            return f"❌ 工具执行多次出错，已停止自动修复：{str(e)}\n请手动检查问题后重试。"
                        error_msg = f"工具执行出错（第{self.error_retry_count}次尝试）：{str(e)}，请分析错误原因尝试修复"
                        if self.verbose:
                            print(f"❌ {error_msg}")
                        self.history.append({
                            "role": "user",
                            "content": error_msg
                        })
                else:
                    # 工具不存在，将错误信息返回给模型，让它修正
                    error_msg = f"错误：不存在名为「{tool_name}」的工具，可用工具：{list(self.tools.keys())}"
                    if self.verbose:
                        print(f"❌ {error_msg}")
                    self.history.append({
                        "role": "user",
                        "content": error_msg
                    })
                continue

            # 3. 判断是否输出了最终答案
            if "答案：" in response:
                answer = response.split("答案：")[-1].strip()
                return answer

            # 4. 格式错误，提示模型按要求输出
            if self.verbose:
                print("⚠️  输出格式错误，提示模型重新输出")
            self.history.append({
                "role": "user",
                "content": "格式错误，请严格按照要求输出：要么输出「思考：...」+「行动：工具|参数」调用工具，要么输出「思考：...」+「答案：...」给出最终答案"
            })

        # 达到最大思考步数仍未得出结论
        return "已达到最大思考步数，未能生成最终答案，你可以换个问法试试"
        


import re
import difflib
from typing import List, Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.llm_client import LLMClient
from tools.base_tool import BaseTool


class ReActAgent:
    def __init__(self, llm: LLMClient, tools: List[BaseTool], verbose: bool = False):
        # 1. 注入大模型客户端（依赖注入，外部创建后传入）
        self.llm = llm
        self.verbose = verbose  # 是否打印详细过程

        # 2. 工具列表转「名称→对象」字典，O(1) 快速查找
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

        # 3. 初始化对话历史列表，存储所有轮次的消息
        self.history: List[dict] = []

        # 4. 构建系统提示词并加入对话历史
        self._init_system_prompt()

    def _scan_project_structure(self, root_path: str, max_depth: int = 3) -> str:
        """扫描项目结构，生成目录树"""
        ignore_dirs = {"venv", "__pycache__", ".git", "node_modules", ".idea", ".vscode", "dist", "build", ".egg-info"}
        result = []
        
        def _scan(path, depth, prefix=""):
            if depth > max_depth:
                return
            try:
                items = sorted(os.listdir(path))
            except:
                return
            # 过滤忽略的目录
            items = [i for i in items if i not in ignore_dirs and not i.startswith(".")]
            for i, item in enumerate(items):
                full_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                result.append(f"{prefix}{current_prefix}{item}{'/' if os.path.isdir(full_path) else ''}")
                if os.path.isdir(full_path):
                    extension = "    " if is_last else "│   "
                    _scan(full_path, depth + 1, prefix + extension)
        
        result.append(os.path.basename(root_path) + "/")
        _scan(root_path, 1)
        return "\n".join(result)

    def _init_system_prompt(self):
        """私有方法：动态生成系统提示词，包含所有工具信息与思考规则"""
        # 拼接所有工具的名称与描述
        tool_info_list = []
        for tool in self.tools.values():
            tool_info_list.append(f"- {tool.name}：{tool.description}")
        tool_info_str = "\n".join(tool_info_list)

        # 扫描项目结构
        project_structure = self._scan_project_structure(os.getcwd())

        system_prompt = f"""你是一个专业的终端代码助手，运行在用户的本地电脑上，帮助用户完成代码开发、调试、文件操作、命令执行等任务。你必须严格按照ReAct思考框架执行，绝对禁止跳步。

当前工作目录：{os.getcwd()}

当前项目结构：
{project_structure}

可用工具列表：
{tool_info_str}

🔴 绝对禁止的行为：
1. 禁止在同一次回复中同时出现「行动：」和「答案：」
2. 禁止提前想象、猜测工具返回结果，必须等工具返回真实结果后再继续思考
3. 禁止跳过工具调用，自己编造结果，所有文件操作、命令执行、代码搜索都必须调用工具完成
4. 每次回复只能有一个「思考：」段落，思考后只能二选一：要么调用工具，要么给出答案
5. 不要输出多余的解释，严格按照格式输出
6. 修改代码前必须先读取原文件内容，绝对禁止在不知道原内容的情况下直接写文件覆盖
7. 修改代码尽量做最小改动，不要重构整个文件，只改需要改的部分

8. 写文件时注意使用UTF-8编码，Python文件要注意缩进正确
9. 同一个错误最多尝试修复2次，修复不了就告诉用户问题在哪，不要无限循环重试

🩹 错误自动修复规则：
1. 如果执行命令报错（比如Python语法错误、缺少依赖包、命令不存在），不要直接把错误返回给用户
2. 先分析错误原因，尝试自己修复：
   - 缺包就执行pip install安装对应依赖
   - 代码语法错误就读取文件，修改错误后重新运行
   - 命令不存在就换正确的命令
3. 最多尝试修复2次，如果还是失败，再告诉用户具体错误和解决方法
8. 写文件时注意使用UTF-8编码，Python文件要注意缩进正确

🟢 正确执行流程：
1. 第一步：思考问题，判断需要调用什么工具，只输出「思考：...」+「行动：工具名|参数」
2. 等待工具返回真实结果
3. 第二步：基于工具返回的真实结果继续思考，如果信息足够就输出答案，不够就继续调用工具
4. 修改文件时：先读原文件→思考修改方案→写文件，绝对不能跳过读文件直接写
5. 信息充足后，输出「思考：我已经获得足够信息，可以给出答案」+「答案：最终内容」

📝 严格输出格式：
需要调用工具时：
思考：你对当前问题的分析和下一步计划
行动：工具名称|参数内容

不需要调用工具/信息足够时：
思考：我已经获得足够信息，可以给出答案
答案：你的最终回答内容
"""

        # 系统消息加入对话历史开头
        self.history.append({"role": "system", "content": system_prompt})

    def _truncate_history(self):
        """上下文自动截断，防止历史太长超过token限制"""
        # 保留系统提示词，最多保留最近20条消息
        if len(self.history) > 21:  # 1条系统提示词 + 20条消息
            self.history = [self.history[0]] + self.history[-20:]

    def _confirm_dangerous_action(self, tool_name: str, input_text: str) -> bool:
        """危险操作确认，返回True表示允许执行，False表示取消"""
        dangerous = False
        reason = ""
        diff_text = ""
        
        # 写文件操作，显示diff
        if tool_name == "file" and input_text.startswith("write|"):
            dangerous = True
            parts = input_text.split("|", 2)
            if len(parts) >= 3:
                file_path = parts[1].strip()
                new_content = parts[2]
                # 处理相对路径
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                reason = f"写入/修改文件：{file_path}"
                # 如果文件存在，生成diff
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            old_content = f.read()
                        # 生成统一diff
                        diff = difflib.unified_diff(
                            old_content.splitlines(keepends=True),
                            new_content.splitlines(keepends=True),
                            fromfile=f"a/{os.path.basename(file_path)}",
                            tofile=f"b/{os.path.basename(file_path)}"
                        )
                        diff_text = "\n变更内容：\n" + "".join(diff)
                    except Exception as e:
                        diff_text = f"\n无法读取原文件生成diff：{str(e)}"
                else:
                    diff_text = f"\n新文件，将创建：{file_path}"
        # 删除类命令
        elif tool_name == "shell":
            dangerous_keywords = ["rm ", "del ", "format", "mkfs", "dd ", "rmdir", "rd "]
            for kw in dangerous_keywords:
                if kw in input_text.lower():
                    dangerous = True
                    reason = f"执行可能删除数据的命令：{input_text}"
                    break
        # Git提交操作
        elif tool_name == "git" and input_text.startswith("commit|"):
            dangerous = True
            commit_msg = input_text.split("|", 1)[1].strip() if "|" in input_text else ""
            reason = f"提交Git代码：{commit_msg}"
        
        if dangerous:
            print(f"\n⚠️  即将执行危险操作：{reason}")
            if diff_text:
                print(diff_text)
            confirm = input("是否确认执行？(y/N): ").strip().lower()
            return confirm == "y"
        return True

    def reset(self):
        """重置对话历史，开始新的会话"""
        self.history = [self.history[0]]  # 保留系统提示词

    def run(self, query: str) -> str:
        # 将用户问题加入对话历史
        self.history.append({"role": "user", "content": query})
        max_steps = 10  # 最大思考步数，防止模型无限循环

        for step in range(max_steps):
            # 自动截断过长的历史
            self._truncate_history()

            if self.verbose:
                print(f"\n🤔 第{step+1}步思考中...")
                print("模型输出：")

            # 1. 流式调用大模型，实时打印输出
            response = ""
            for chunk in self.llm.chat_stream(self.history):
                response += chunk
                if self.verbose:
                    print(chunk, end="", flush=True)
            response = response.strip()
            self.history.append({"role": "assistant", "content": response})

            if self.verbose:
                print("\n" + "-"*50)

            # 2. 优先判断是否需要调用工具（必须先判断行动，防止跳步）
            if "行动：" in response:
                action_part = response.split("行动：")[-1].strip().split("\n")[0].strip()
                if "|" in action_part:
                    tool_name, tool_args = action_part.split("|", 1)
                    tool_name = tool_name.strip()
                    tool_args = tool_args.strip()
                else:
                    tool_name = action_part.strip()
                    tool_args = ""

                if self.verbose:
                    print(f"🔧 调用工具：{tool_name}，参数：{tool_args}")

                # 危险操作确认
                if not self._confirm_dangerous_action(tool_name, tool_args):
                    self.history.append({
                        "role": "user",
                        "content": "操作已被用户取消，请根据用户的指示调整"
                    })
                    continue

                if tool_name in self.tools:
                    try:
                        # 执行工具
                        tool_result = self.tools[tool_name].run(tool_args)
                        if self.verbose:
                            print(f"✅ 工具返回：{tool_result[:200]}..." if len(tool_result) > 200 else f"✅ 工具返回：{tool_result}")
                            print("-"*50)
                        # 将结果加入历史，进入下一轮思考
                        self.history.append({
                            "role": "user",
                            "content": f"工具返回结果：{tool_result}"
                        })
                    except Exception as e:
                        error_msg = f"工具执行出错：{str(e)}"
                        if self.verbose:
                            print(f"❌ {error_msg}")
                        self.history.append({
                            "role": "user",
                            "content": error_msg
                        })
                else:
                    # 工具不存在，将错误信息返回给模型，让它修正
                    error_msg = f"错误：不存在名为「{tool_name}」的工具，可用工具：{list(self.tools.keys())}"
                    if self.verbose:
                        print(f"❌ {error_msg}")
                    self.history.append({
                        "role": "user",
                        "content": error_msg
                    })
                continue

            # 3. 判断是否输出了最终答案
            if "答案：" in response:
                answer = response.split("答案：")[-1].strip()
                return answer

            # 4. 格式错误，提示模型按要求输出
            if self.verbose:
                print("⚠️  输出格式错误，提示模型重新输出")
            self.history.append({
                "role": "user",
                "content": "格式错误，请严格按照要求输出：要么输出「思考：...」+「行动：工具|参数」调用工具，要么输出「思考：...」+「答案：...」给出最终答案"
            })

        # 达到最大思考步数仍未得出结论
        return "已达到最大思考步数，未能生成最终答案，你可以换个问法试试"
