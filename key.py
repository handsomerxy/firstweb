# Please install OpenAI SDK first: `pip3 install openai`
from openai import OpenAI
import time
import json
from datetime import datetime
import os

client = OpenAI(
  base_url="https://api.tokenpony.cn/v1",
  api_key="sk-ef44e1b5f2174411acaa32c79d547af8", #替换为您的API Key
)

# 配置参数
MAX_TOKENS_PER_MESSAGE = 1000  # 每条消息的最大token数
MAX_TOTAL_TOKENS = 4000       # 对话历史的最大总token数
MAX_MESSAGES = 10             # 保留的最大消息数量（不包括系统消息）
LOG_DIR = "logs"               # 日志目录
CONVERSATIONS_DIR = "conversations"  # 对话保存目录

# 确保目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# 日志记录函数
def log_message(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOG_DIR, f"chatbot_{datetime.now().strftime('%Y-%m-%d')}.log")
    log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
    
    # 写入日志文件
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # 如果是错误或警告，同时打印到控制台
    if level in ["error", "warning"]:
        print(f"[{timestamp}] [{level.upper()}] {message}")

# 打字机效果函数
def print_with_typewriter(text, delay=0.03):
    """
    打字机效果打印文本
    
    Args:
        text: 要打印的文本
        delay: 每个字符间的延迟时间（秒）
    """
    try:
        import sys
        for char in text:
            print(char, end="", flush=True)
            # 根据字符调整延迟，让标点符号停顿时间稍长
            if char in [".", "。", "!", "！", "?", "？", ";", "；", ":", "："]:
                time.sleep(delay * 3)
            elif char in [",", "，", "、"]:
                time.sleep(delay * 2)
            elif char == "\n":
                time.sleep(delay * 10)
            else:
                time.sleep(delay)
        print()  # 最后换行
    except KeyboardInterrupt:
        print("\n")  # 确保中断后也换行

# 保存对话历史
def save_conversation(conversation_history, filename=None):
    try:
        # 如果没有提供文件名，使用当前时间生成
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        # 确保文件名以.json结尾
        if not filename.endswith(".json"):
            filename += ".json"
        
        # 构建完整路径
        filepath = os.path.join(CONVERSATIONS_DIR, filename)
        
        # 保存对话历史
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
        
        log_message("info", f"对话已保存到 {filepath}")
        return True, filepath
    except Exception as e:
        log_message("error", f"保存对话时出错: {str(e)}")
        return False, str(e)

# 加载对话历史
def load_conversation(filename):
    try:
        # 确保文件名以.json结尾
        if not filename.endswith(".json"):
            filename += ".json"
        
        # 构建完整路径
        filepath = os.path.join(CONVERSATIONS_DIR, filename)
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return False, f"文件 {filepath} 不存在"
        
        # 加载对话历史
        with open(filepath, "r", encoding="utf-8") as f:
            conversation_history = json.load(f)
        
        log_message("info", f"对话已从 {filepath} 加载")
        return True, conversation_history
    except json.JSONDecodeError:
        log_message("error", f"无法解析JSON文件 {filename}")
        return False, f"文件 {filename} 不是有效的JSON文件"
    except Exception as e:
        log_message("error", f"加载对话时出错: {str(e)}")
        return False, str(e)

# 列出所有保存的对话
def list_conversations():
    try:
        # 获取所有.json文件
        files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith(".json")]
        
        # 按修改时间排序，最新的在前
        files.sort(key=lambda x: os.path.getmtime(os.path.join(CONVERSATIONS_DIR, x)), reverse=True)
        
        return True, files
    except Exception as e:
        log_message("error", f"列出对话时出错: {str(e)}")
        return False, str(e)

# 简单的token估算函数（实际应用中可使用更准确的tokenizer）
def count_tokens(text):
    # 一个简单的估算，实际token数可能会有所不同
    return len(text) // 4  # 粗略估算：1 token ≈ 4个字符

# 限制对话历史长度
def limit_conversation_history(conversation_history):
    # 保留系统消息
    system_messages = [msg for msg in conversation_history if msg['role'] == 'system']
    user_assistant_messages = [msg for msg in conversation_history if msg['role'] != 'system']
    
    # 如果消息数量超过限制，只保留最近的消息
    if len(user_assistant_messages) > MAX_MESSAGES:
        user_assistant_messages = user_assistant_messages[-MAX_MESSAGES:]
    
    # 重新组合消息历史
    limited_history = system_messages + user_assistant_messages
    
    # 计算总token数并限制
    total_tokens = sum(count_tokens(msg['content']) for msg in limited_history)
    
    # 如果总token数超过限制，从最早的用户/助手消息开始删除
    while total_tokens > MAX_TOTAL_TOKENS and len(user_assistant_messages) > 2:
        removed_message = user_assistant_messages.pop(0)
        total_tokens -= count_tokens(removed_message['content'])
        limited_history = system_messages + user_assistant_messages
    
    return limited_history

# 初始化对话历史
conversation_history = [
    {"role": "system", "content": "You are a helpful AI assistant. Please respond clearly and concisely."}
]

# 记录启动日志
log_message("info", "聊天机器人启动成功")

# 只有当直接运行此文件时才执行主程序
if __name__ == "__main__":
    print("欢迎使用聊天机器人！")
    print("输入 'exit' 或 '退出' 结束对话。")
    print("输入 'save' 保存当前对话。")
    print("输入 'load' 加载之前的对话。")
    print("输入 'list' 查看所有保存的对话。")
    print("输入 'system' 修改AI的系统提示词。")
    print("=" * 50)

    while True:
        # 获取用户输入
        try:
            user_input = input("用户: ").strip()
        except KeyboardInterrupt:
            print("\n\n程序被用户中断，再见！")
            log_message("info", "程序被用户中断")
            break
        except Exception as e:
            log_message("error", f"获取用户输入时出错: {str(e)}")
            print("AI: 抱歉，处理您的输入时出现了问题。")
            continue
        
        # 检查特殊命令
        if user_input.lower() in ["exit", "退出"]:
            print("感谢使用，再见！")
            log_message("info", "程序正常退出")
            break
        
        elif user_input.lower() == "system":
            print("当前系统提示词：")
            current_system_message = next((msg['content'] for msg in conversation_history if msg['role'] == 'system'), "未设置")
            print(current_system_message)
            print("\n请输入新的系统提示词（留空则保持不变）: ")
            try:
                new_system_prompt = input().strip()
                if new_system_prompt:
                    # 移除现有的系统消息
                    conversation_history = [msg for msg in conversation_history if msg['role'] != 'system']
                    # 添加新的系统消息
                    conversation_history.insert(0, {"role": "system", "content": new_system_prompt})
                    print("AI: ", end="", flush=True)
                    print_with_typewriter("系统提示词已成功更新！")
                    log_message("info", f"系统提示词已更新: {new_system_prompt[:100]}...")
                else:
                    print("AI: ", end="", flush=True)
                    print_with_typewriter("系统提示词未更改。")
            except KeyboardInterrupt:
                print("\n操作已取消")
            print("=" * 50)
            continue
        
        elif user_input.lower() == "save":
            print("请输入保存名称（留空使用默认名称）: ")
            try:
                save_name = input().strip()
                success, result = save_conversation(conversation_history, save_name if save_name else None)
                if success:
                    print("AI: ", end="", flush=True)
                    print_with_typewriter(f"对话已成功保存到 {result}")
                else:
                    print("AI: ", end="", flush=True)
                    print_with_typewriter(f"保存对话失败 - {result}")
            except KeyboardInterrupt:
                print("\n保存操作已取消")
            print("=" * 50)
            continue
        
        elif user_input.lower() == "load":
            # 列出所有对话
            success, files = list_conversations()
            if success:
                if not files:
                    print("AI: ", end="", flush=True)
                    print_with_typewriter("没有找到保存的对话。")
                else:
                    print("保存的对话列表:")
                    for i, file in enumerate(files, 1):
                        # 获取文件修改时间
                        mtime = os.path.getmtime(os.path.join(CONVERSATIONS_DIR, file))
                        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{i}. {file} ({mtime_str})")
                    
                    print("\n请输入要加载的对话编号或文件名: ")
                    try:
                        load_input = input().strip()
                        # 尝试解析为编号
                        try:
                            index = int(load_input) - 1
                            if 0 <= index < len(files):
                                filename = files[index]
                            else:
                                print("AI: ", end="", flush=True)
                                print_with_typewriter("无效的编号。")
                                print("=" * 50)
                                continue
                        except ValueError:
                            # 不是编号，直接作为文件名
                            filename = load_input
                        
                        success, result = load_conversation(filename)
                        if success:
                            conversation_history = result
                            print("AI: ", end="", flush=True)
                            print_with_typewriter("对话已成功加载。")
                        else:
                            print("AI: ", end="", flush=True)
                            print_with_typewriter(f"加载对话失败 - {result}")
                    except KeyboardInterrupt:
                        print("\n加载操作已取消")
            else:
                print("AI: ", end="", flush=True)
                print_with_typewriter(f"列出对话失败 - {files}")
            print("=" * 50)
            continue
        
        elif user_input.lower() == "list":
            success, files = list_conversations()
            if success:
                if not files:
                    print("AI: ", end="", flush=True)
                    print_with_typewriter("没有找到保存的对话。")
                else:
                    print("保存的对话列表:")
                    for i, file in enumerate(files, 1):
                        mtime = os.path.getmtime(os.path.join(CONVERSATIONS_DIR, file))
                        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{i}. {file} ({mtime_str})")
            else:
                print("AI: ", end="", flush=True)
                print_with_typewriter(f"列出对话失败 - {files}")
            print("=" * 50)
            continue
        
        # 检查输入是否为空
        if not user_input:
            print("AI: ", end="", flush=True)
            print_with_typewriter("请输入您的问题或需求。")
            continue
        
        try:
            # 检查用户输入长度
            if len(user_input) > MAX_TOKENS_PER_MESSAGE * 4:  # 粗略估算
                print("AI: ", end="", flush=True)
                print_with_typewriter("您的消息太长了，请尝试缩短输入内容。")
                print("=" * 50)
                log_message("warning", "用户输入过长，已拒绝处理")
                continue
            
            log_message("info", f"用户输入: {user_input[:100]}..." if len(user_input) > 100 else f"用户输入: {user_input}")
            
            # 将用户输入添加到对话历史
            conversation_history.append({"role": "user", "content": user_input})
            
            # 限制对话历史长度
            conversation_history = limit_conversation_history(conversation_history)
            
            # 添加请求超时处理
            try:
                # 调用OpenAI API获取响应
                response = client.chat.completions.create(
                    model="deepseek-v3.2-exp", #替换为您要使用的模型名称
                    messages=conversation_history,
                    temperature=0.7,  # 设置温度以增加响应的多样性
                    max_tokens=512,   # 增加最大 tokens 以支持更长的响应
                    stream=False,
                    timeout=30  # 设置30秒超时
                )
            except TimeoutError:
                log_message("error", "API请求超时")
                print("AI: ", end="", flush=True)
                print_with_typewriter("服务器响应超时，请稍后再试。")
                print("=" * 50)
                conversation_history.pop()  # 移除最后添加的用户输入
                continue
            
            # 提取并打印AI响应
            ai_response = response.choices[0].message.content.strip()
            print("AI: ", end="", flush=True)
            print_with_typewriter(ai_response)
            print("=" * 50)
            
            log_message("info", f"AI响应: {ai_response[:100]}..." if len(ai_response) > 100 else f"AI响应: {ai_response}")
            
            # 将AI响应添加到对话历史
            conversation_history.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            error_message = str(e)
            log_message("error", f"处理对话时出错: {error_message}")
            
            # 根据不同错误类型提供友好提示
            if "API key" in error_message:
                print("AI: ", end="", flush=True)
                print_with_typewriter("认证失败，请检查您的API密钥是否正确。")
            elif "rate limit" in error_message.lower():
                print("AI: ", end="", flush=True)
                print_with_typewriter("当前请求频率过高，请稍后再试。")
            elif "context length" in error_message.lower():
                print("AI: ", end="", flush=True)
                print_with_typewriter("对话内容过长，请尝试开始一个新的对话。")
            else:
                print("AI: ", end="", flush=True)
                print_with_typewriter(f"抱歉，发生了错误 - {error_message[:100]}")
            
            print("=" * 50)
            # 移除最后添加的用户输入，避免影响后续对话
            if len(conversation_history) > 1:  # 确保至少保留系统消息
                conversation_history.pop()