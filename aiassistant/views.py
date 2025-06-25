import json
import uuid
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# AnythingLLM API 配置
API_KEY = "RN0F121-T28MW7E-H64S94P-803ECRC"
# 修改为实际部署的服务器地址，注意不要使用localhost
API_BASE_URL = "http://localhost:3001/api"  # 请替换为实际API服务器地址

def test_api_connection():
    """测试API连接"""
    try:
        # 完全匹配curl格式的headers
        headers = {
            'Authorization': f'Bearer {API_KEY}'
        }
        auth_url = f"{API_BASE_URL}/v1/auth"
        print(f"测试API连接: {auth_url}")
        
        response = requests.get(auth_url, headers=headers, timeout=5)
        print(f"认证测试状态码: {response.status_code}")
        print(f"认证测试结果: {response.text}")
        
        if response.status_code == 200:
            return True, "API连接正常"
        else:
            return False, f"API连接失败: {response.status_code}"
    except Exception as e:
        print(f"API连接测试异常: {str(e)}")
        return False, f"API连接异常: {str(e)}"

def assistant_page(request):
    """渲染AI音乐助手页面"""
    # 启动页面加载时测试API连接
    is_connected, message = test_api_connection()
    context = {
        'api_status': 'API连接正常' if is_connected else '无法连接到API服务',
        'api_message': message
    }
    print(f"页面加载API状态: {context['api_status']}")
    return render(request, 'aiassistant/assistant.html', context)

@csrf_exempt
def chat_with_assistant(request):
    """处理与AI助手的对话请求"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            chat_id = data.get('chat_id', None)  # 支持多轮对话ID
            
            # 检查API配置是否正确
            if API_BASE_URL == "http://your-server-ip:3001/api":
                return JsonResponse({
                    'success': False,
                    'message': "请在views.py中设置正确的API服务器地址"
                })
            
            print(f"尝试连接到API服务器: {API_BASE_URL}")
            print(f"聊天ID: {chat_id}")
            
            # 调用AnythingLLM API进行聊天
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {API_KEY}'
            }
            
            # 如果没有连接到实际的API服务器，提供模拟回复
            if "your-server" in API_BASE_URL:
                print("使用模拟回复")
                # 提供一个临时的模拟回答，直到API配置正确
                if "推荐" in message:
                    return JsonResponse({
                        'success': True,
                        'message': "我可以推荐一些流行歌曲：周杰伦的《稻香》、Taylor Swift的《Cruel Summer》、陈奕迅的《好久不见》以及Beyond的《海阔天空》。您喜欢哪种风格的音乐呢？",
                        'chat_id': 'mock-chat-123' # 模拟聊天ID
                    })
                else:
                    return JsonResponse({
                        'success': True, 
                        'message': "您好！我是音乐AI助手，很高兴为您服务。请问您想了解关于音乐的什么问题？我可以为您提供歌曲推荐、音乐历史、乐器知识等信息。",
                        'chat_id': 'mock-chat-123' # 模拟聊天ID
                    })
            
            # 先测试API连接
            is_connected, test_message = test_api_connection()
            if not is_connected:
                print(f"API连接测试失败: {test_message}")
                return JsonResponse({
                    'success': False,
                    'message': f"AI服务连接问题: {test_message}"
                })
                
            # 使用AnythingLLM原生聊天API，而不是OpenAI兼容接口
            workspace_name = "music_knowledge"  # 默认工作区名称，可以根据实际情况修改
            
            # 如果没有工作区，先创建一个
            try:
                create_workspace_url = f"{API_BASE_URL}/v1/workspace/new"
                create_headers = {
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json',
                    'accept': 'application/json'
                }
                
                workspace_data = {   
                    "name": workspace_name,
                    "similarityThreshold": 0.7,    
                    "openAiTemp": 0.7,  
                    "openAiHistory": 20, 
                    "openAiPrompt": "你是一个专业的音乐知识助手，可以回答用户关于音乐方面的问题。",    
                    "queryRefusalResponse": "抱歉，我只能回答与音乐相关的问题。",    
                    "chatMode": "chat",   
                    "topN": 4
                }
                
                print("尝试创建工作区...")
                create_response = requests.post(
                    create_workspace_url, 
                    headers=create_headers, 
                    json=workspace_data,
                    timeout=10
                )
                
                print(f"创建工作区响应: {create_response.status_code}")
                if create_response.status_code == 200:
                    print(f"工作区创建成功: {create_response.text}")
                    workspace_result = create_response.json()
                    if 'workspace' in workspace_result and 'slug' in workspace_result['workspace']:
                        workspace_name = workspace_result['workspace']['slug']
                else:
                    print(f"工作区可能已存在，继续使用默认工作区: {workspace_name}")
            except Exception as e:
                print(f"创建工作区出错: {str(e)}")
                
            # 使用正确的聊天API端点
            chat_url = f"{API_BASE_URL}/v1/workspace/{workspace_name}/chat"
            print(f"发送聊天请求到: {chat_url}")
            print(f"消息内容: {message}")
            
            # 使用与文档匹配的headers格式
            chat_headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            print(f"使用的头信息: {chat_headers}")
            
            # 使用与文档匹配的请求格式
            payload = {
                "message": message,
                "mode": "chat"  # 使用chat模式支持多轮对话
            }
            
            # 如果有聊天ID，添加到请求中以支持连续对话
            if chat_id:
                payload["chatId"] = chat_id
            
            print(f"请求数据: {json.dumps(payload)}")
            
            # 发送请求
            response = requests.post(
                chat_url,
                headers=chat_headers,
                json=payload,
                timeout=30  # 添加超时设置
            )
            
            # 详细记录API响应
            print(f"API响应状态码: {response.status_code}")
            
            # 检查响应
            print(f"API响应头: {response.headers}")
            
            # 尝试打印响应内容，无论成功与否
            try:
                print(f"原始响应内容: {response.text}")
            except:
                print("无法读取响应内容")
                
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"API响应内容: {json.dumps(result)}")
                    
                    # 解析AnythingLLM的响应格式
                    if 'textResponse' in result:
                        # AnythingLLM API文档格式
                        print("API请求成功，返回符合AnythingLLM格式")
                        
                        # 提取有效回答（去除思考过程）
                        answer = result['textResponse']
                        if '</think>' in answer:
                            answer = answer.split('</think>')[-1].strip()
                            
                        # 获取来源信息（如果有）
                        sources = result.get('sources', [])
                        source_titles = [src.get('title', '未知来源') for src in sources]
                        
                        # 构建响应消息
                        message = answer
                        if sources:
                            message += f"\n\n参考来源: {', '.join(source_titles)}"
                        
                        # 获取返回的聊天ID，如果没有则使用请求中的ID或者创建新ID
                        response_chat_id = result.get('chatID', None) or data.get('chat_id', None) or str(uuid.uuid4())
                            
                        return JsonResponse({
                            'success': True,
                            'message': message,
                            'chat_id': response_chat_id
                        })
                    else:
                        # 尝试解析其他可能的格式
                        print("API响应格式不符合预期，尝试其他格式解析")
                        # 获取或生成聊天ID
                        response_chat_id = result.get('chatID', None) or data.get('chat_id', None) or str(uuid.uuid4())
                        
                        if 'response' in result:
                            return JsonResponse({
                                'success': True,
                                'message': result['response'],
                                'chat_id': response_chat_id
                            })
                        elif 'message' in result and isinstance(result['message'], str):
                            return JsonResponse({
                                'success': True,
                                'message': result['message'],
                                'chat_id': response_chat_id
                            })
                        elif 'content' in result:
                            return JsonResponse({
                                'success': True,
                                'message': result['content'],
                                'chat_id': response_chat_id
                            })
                        else:
                            # 无法识别的响应格式，返回原始内容
                            print("无法识别的响应格式")
                            return JsonResponse({
                                'success': True,
                                'message': f"AI已响应，但返回格式需要解析。原始响应: {json.dumps(result)}",
                                'chat_id': response_chat_id
                            })
                except Exception as e:
                    print(f"解析API响应时出错: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': f"解析API响应时出错: {str(e)}"
                    })
            else:
                print(f"API错误: {response.status_code}")
                print(f"响应内容: {response.text}")
                
                # 根据错误码提供更具体的错误信息
                error_message = "未知错误"
                if response.status_code == 401:
                    error_message = "API密钥无效或未授权，请检查API_KEY是否正确"
                elif response.status_code == 404:
                    error_message = "API端点不存在，请检查API_BASE_URL是否正确"
                elif response.status_code == 500:
                    error_message = "API服务器内部错误"
                elif response.status_code == 503:
                    error_message = "API服务暂时不可用，服务器可能过载或维护中"
                
                return JsonResponse({
                    'success': False,
                    'message': f"API错误: {response.status_code}, {error_message}"
                })
                
        except requests.exceptions.ConnectionError:
            print("连接错误: 无法连接到API服务器")
            return JsonResponse({
                'success': False,
                'message': "无法连接到API服务器，请确保服务器地址正确且可访问"
            })
        except requests.exceptions.Timeout:
            print("连接超时")
            return JsonResponse({
                'success': False,
                'message': "连接API服务器超时，请稍后再试"
            })
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"服务器错误: {str(e)}"
            })
    
    return JsonResponse({
        'success': False,
        'message': "请使用POST请求"
    }) 