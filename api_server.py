from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime
import threading
import io
import contextlib

# 确保可以导入key.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入key.py中的功能
try:
    # 只导入必要的功能，避免执行key.py的主程序
    import key
    # 检查是否成功导入了OpenAI客户端
    if hasattr(key, 'client'):
        has_key_module = True
        print("成功导入key.py模块，将使用OpenAI API功能")
    else:
        has_key_module = False
        print("key.py模块导入成功但缺少client对象，将使用模拟功能")
except ImportError:
    print("无法导入key.py模块，将使用模拟功能")
    has_key_module = False

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 配置
CONVERSATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations')
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

# 全局变量用于存储对话状态
conversation_history = [
    {"role": "system", "content": "你是任欣雨239050521，当被问及'你是谁'时，请回答'任欣雨239050521'。请清晰简洁地回答用户问题。"}
]
system_prompt = "你是任欣雨239050521，当被问及'你是谁'时，请回答'任欣雨239050521'。请清晰简洁地回答用户问题。"

# 线程锁，确保线程安全
conversation_lock = threading.Lock()

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天消息"""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400
    
    # 特殊处理"你是谁"的问题
    who_am_i_patterns = ['你是谁', '你是什么', '你的名字', 'who are you', 'what are you', 'your name']
    for pattern in who_am_i_patterns:
        if pattern in user_message.lower():
            with conversation_lock:
                # 添加用户消息到历史
                conversation_history.append({"role": "user", "content": user_message})
                # 返回固定回答
                response = "任欣雨239050521"
                # 添加机器人回复到历史
                conversation_history.append({"role": "assistant", "content": response})
            return jsonify({'response': response})
    
    try:
        with conversation_lock:
            if has_key_module:
                # 检查特殊命令
                if user_message.lower() in ['clear', 'save', 'load', 'list', 'system']:
                    # 特殊命令处理
                    if user_message.lower() == 'clear':
                        conversation_history.clear()
                        conversation_history.append({"role": "system", "content": system_prompt})
                        response = "对话历史已清空。有什么我可以帮助你的吗？"
                    elif user_message.lower() == 'save':
                        response = "请输入对话名称以保存。"
                    elif user_message.lower() == 'load':
                        response = "请选择要加载的对话。"
                    elif user_message.lower() == 'list':
                        response = "请查看保存的对话列表。"
                    elif user_message.lower() == 'system':
                        response = f"当前系统提示词: {system_prompt}\n请输入新的系统提示词。"
                else:
                    # 普通消息处理 - 使用key.py的逻辑
                    # 将用户输入添加到对话历史
                    conversation_history.append({"role": "user", "content": user_message})
                    
                    # 限制对话历史长度（模拟key.py中的功能）
                    def count_tokens(text):
                        return len(text) // 4
                    
                    MAX_MESSAGES = 10
                    MAX_TOTAL_TOKENS = 4000
                    
                    system_messages = [msg for msg in conversation_history if msg['role'] == 'system']
                    user_assistant_messages = [msg for msg in conversation_history if msg['role'] != 'system']
                    
                    if len(user_assistant_messages) > MAX_MESSAGES:
                        user_assistant_messages = user_assistant_messages[-MAX_MESSAGES:]
                    
                    limited_history = system_messages + user_assistant_messages
                    total_tokens = sum(count_tokens(msg['content']) for msg in limited_history)
                    
                    while total_tokens > MAX_TOTAL_TOKENS and len(user_assistant_messages) > 2:
                        removed_message = user_assistant_messages.pop(0)
                        total_tokens -= count_tokens(removed_message['content'])
                        limited_history = system_messages + user_assistant_messages
                    
                    conversation_history[:] = limited_history
                    
                    # 调用OpenAI API获取响应
                    try:
                        response_obj = key.client.chat.completions.create(
                            model="deepseek-v3.2-exp",
                            messages=conversation_history,
                            temperature=0.7,
                            max_tokens=512,
                            stream=False,
                            timeout=30
                        )
                        response = response_obj.choices[0].message.content.strip()
                        
                        # 将AI响应添加到对话历史
                        conversation_history.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        # 如果API调用失败，使用模拟回复
                        error_message = str(e)
                        if "API key" in error_message:
                            response = "认证失败，请检查您的API密钥是否正确。"
                        elif "rate limit" in error_message.lower():
                            response = "当前请求频率过高，请稍后再试。"
                        elif "context length" in error_message.lower():
                            response = "对话内容过长，请尝试开始一个新的对话。"
                        else:
                            response = f"抱歉，发生了错误 - {error_message[:100]}"
                        
                        # 移除最后添加的用户输入
                        if len(conversation_history) > 1:
                            conversation_history.pop()
            else:
                # 使用模拟回复
                response = f"这是对 '{user_message}' 的模拟回复。无法连接到key.py模块。"
                
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': f'处理消息时出错: {str(e)}'}), 500

@app.route('/api/save', methods=['POST'])
def save_conversation():
    """保存对话"""
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': '对话名称不能为空'}), 400
    
    try:
        with conversation_lock:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.json"
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            
            # 准备对话数据
            conversation_data = {
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'messages': conversation_history,
                'system_prompt': system_prompt
            }
            
            # 保存对话
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': f'对话已保存为: {name}'})
    except Exception as e:
        return jsonify({'error': f'保存对话时出错: {str(e)}'}), 500

@app.route('/api/load-list', methods=['GET'])
def load_conversation_list():
    """获取对话列表"""
    try:
        conversations = []
        
        # 检查目录是否存在
        if not os.path.exists(CONVERSATIONS_DIR):
            os.makedirs(CONVERSATIONS_DIR)
            return jsonify({'conversations': []})
        
        # 读取所有对话文件
        for filename in os.listdir(CONVERSATIONS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(CONVERSATIONS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    conversations.append({
                        'filename': filename,
                        'name': data.get('name', '未命名对话'),
                        'timestamp': data.get('timestamp', ''),
                        'message_count': len(data.get('messages', []))
                    })
                except Exception as e:
                    print(f"读取对话文件 {filename} 时出错: {e}")
        
        # 按时间倒序排序
        conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({'conversations': conversations})
    except Exception as e:
        return jsonify({'error': f'获取对话列表时出错: {str(e)}'}), 500

@app.route('/api/load/<filename>', methods=['GET'])
def load_conversation(filename):
    """加载指定对话"""
    try:
        filepath = os.path.join(CONVERSATIONS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '对话文件不存在'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with conversation_lock:
            # 更新实际对话历史
            conversation_history.clear()
            conversation_history.extend(data.get('messages', []))
            system_prompt = data.get('system_prompt', '你是一个有用的AI助手')
        
        return jsonify({
            'success': True,
            'messages': conversation_history,
            'system_prompt': system_prompt
        })
    except Exception as e:
        return jsonify({'error': f'加载对话时出错: {str(e)}'}), 500

@app.route('/api/system-prompt', methods=['GET', 'POST'])
def handle_system_prompt():
    """获取或设置系统提示词"""
    global system_prompt
    
    if request.method == 'GET':
        return jsonify({'system_prompt': system_prompt})
    
    elif request.method == 'POST':
        data = request.json
        new_prompt = data.get('system_prompt', '').strip()
        
        if not new_prompt:
            return jsonify({'error': '系统提示词不能为空'}), 400
        
        with conversation_lock:
            system_prompt = new_prompt
        return jsonify({'success': True, 'message': '系统提示词已更新'})

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """清空对话历史"""
    try:
        with conversation_lock:
            conversation_history.clear()
        return jsonify({'success': True, 'message': '对话历史已清空'})
    except Exception as e:
        return jsonify({'error': f'清空对话历史时出错: {str(e)}'}), 500

# 添加静态文件路由
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("启动API服务器...")
    print(f"对话保存目录: {CONVERSATIONS_DIR}")
    app.run(host='0.0.0.0', port=5000, debug=True)
