# # main.py
# import os
# import uuid
# from datetime import datetime
# from typing import Optional, Dict

# from fastapi import FastAPI, Depends, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# from sqlalchemy.orm import Session
# from openai import OpenAI

# from database import get_db, User, Conversation
# from dotenv import load_dotenv

# # 加载 .env 文件
# load_dotenv()

# # 初始化 FastAPI
# app = FastAPI(title="AI Chat Platform")

# # CORS（开发用）
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 检查 API Key
# DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
# if not DASHSCOPE_API_KEY:
#     raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

# # 支持的模型配置
# MODELS_CONFIG = {
#     "qwen-doc-turbo": {
#         "name": "qwen-doc-turbo",
#         "api_key_env": "DASHSCOPE_API_KEY",
#         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
#         "system_prompt": """你是一个智能电商购物助手，请根据以下规则与用户进行多轮对话，最终推荐一个商品：
# 目标导向：你的最终目标是推荐一个特定商品（该商品真实存在且用户曾购买过），但不要一开始就透露。
# 知识驱动：所有提问必须基于商品的知识图谱信息，包括类别、品牌、属性（如"健康""便携""高性价比"）等实体。
# 由粗到细：先从宽泛的类别或需求开始提问（例如："您想买饮料吗？"），再逐步聚焦到具体品牌或属性（例如："您偏好可口可乐吗？"、"需要低糖的吗？"）。
# 问答形式：每轮只提一个问题，且必须是是非问句（Yes/No Question），例如："您喜欢健康一点的吗？"
# 用户偏好模拟：假设用户对目标商品具备正向偏好。若问题涉及目标商品的真实属性，则用户回答"是"；否则回答"否"。
# 自然流畅：语言要口语化、友好，避免机械重复，适时使用表情或鼓励性语句。
# 请开始第一轮提问。"""
#     },
#     "baidu/ernie-4.5-0.3b": {
#         "name": "baidu/ernie-4.5-0.3b",
#         "api_key_env": "OPENAI_API_KEY",
#         "base_url": "https://api.ppio.com/openai",
#         "system_prompt": """你是一个智能电商购物助手，请根据以下规则与用户进行多轮对话，最终推荐一个商品：
# 目标导向：你的最终目标是推荐一个特定商品（该商品真实存在且用户曾购买过），但不要一开始就透露。
# 知识驱动：所有提问必须基于商品的知识图谱信息，包括类别、品牌、属性（如"健康""便携""高性价比"）等实体。
# 由粗到细：先从宽泛的类别或需求开始提问（例如："您想买饮料吗？"），再逐步聚焦到具体品牌或属性（例如："您偏好可口可乐吗？"、"需要低糖的吗？"）。
# 问答形式：每轮只提一个问题，且必须是是非问句（Yes/No Question），例如："您喜欢健康一点的吗？"
# 用户偏好模拟：假设用户对目标商品具备正向偏好。若问题涉及目标商品的真实属性，则用户回答"是"；否则回答"否"。
# 自然流畅：语言要口语化、友好，避免机械重复，适时使用表情或鼓励性语句。
# 请开始第一轮提问。"""
#     }
# }

# # 请求模型
# class ChatRequest(BaseModel):
#     user_id: Optional[str] = None
#     message: str
#     model: str = "qwen-doc-turbo"

# class UserCreateRequest(BaseModel):
#     user_id: Optional[str] = None

# class ModelSwitchRequest(BaseModel):
#     user_id: str
#     model: str

# class RatingRequest(BaseModel):
#     user_id: str
#     conversation_id: int
#     rating: float

# class ServiceRatingRequest(BaseModel):
#     user_id: str
#     rating: float

# def get_or_create_user(db: Session, user_id: Optional[str] = None):
#     """获取或创建用户"""
#     if user_id:
#         user = db.query(User).filter(User.user_id == user_id).first()
#         if user:
#             return user
    
#     # 创建新用户
#     new_user_id = user_id or str(uuid.uuid4())
#     user = User(user_id=new_user_id)
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user

# # 修改 main.py 中的 call_model_api 函数
# def call_model_api(model_config: Dict, message: str, history: list = None) -> str:
#     """调用大模型API"""
#     api_key = os.getenv(model_config["api_key_env"])
#     if not api_key:
#         raise ValueError(f"请设置环境变量 {model_config['api_key_env']}")
    
#     # 添加调试信息
#     print(f"调用模型: {model_config.get('name')}")
#     print(f"API Base URL: {model_config.get('base_url')}")
#     print(f"API Key 长度: {len(api_key) if api_key else 0}")
    
#     try:
#         client = OpenAI(
#             api_key=api_key,
#             base_url=model_config["base_url"],
#         )
        
#         # 构建消息历史
#         messages = [
#             {"role": "system", "content": model_config["system_prompt"]}
#         ]
        
#         # 添加上下文历史（如果有）
#         if history:
#             for h in history:
#                 messages.append({"role": "user", "content": h.user_message})
#                 messages.append({"role": "assistant", "content": h.ai_response})
        
#         # 添加当前消息
#         messages.append({"role": "user", "content": message})
        
#         print(f"发送的消息数量: {len(messages)}")
#         print(f"系统提示: {messages[0]['content'][:100]}...")
        
#         completion = client.chat.completions.create(
#             model=model_config["name"],  # 使用配置中的name字段
#             messages=messages,
#             timeout=30.0
#         )
        
#         response = completion.choices[0].message.content
#         print(f"AI响应: {response[:100]}...")
#         return response
        
#     except Exception as e:
#         print(f"API调用错误详情: {str(e)}")
#         print(f"错误类型: {type(e)}")
#         raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")

# @app.post("/create-user")
# def create_user(req: UserCreateRequest, db: Session = Depends(get_db)):
#     """创建新用户"""
#     user = get_or_create_user(db, req.user_id)
#     return {
#         "user_id": user.user_id,
#         "created_at": user.created_at,
#         "current_model": user.current_model
#     }

# @app.post("/switch-model")
# def switch_model(req: ModelSwitchRequest, db: Session = Depends(get_db)):
#     """切换用户使用的模型"""
#     user = db.query(User).filter(User.user_id == req.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="用户未找到")
    
#     if req.model not in MODELS_CONFIG:
#         raise HTTPException(status_code=400, detail="不支持的模型")
    
#     user.current_model = req.model
#     db.commit()
#     return {"status": "ok", "current_model": req.model}

# @app.get("/available-models")
# def get_available_models():
#     """获取可用的模型列表"""
#     return {
#         "models": [
#             {
#                 "id": model_id,
#                 "name": config["name"],
#                 "description": f"{config['name']} 模型"
#             }
#             for model_id, config in MODELS_CONFIG.items()
#         ]
#     }

# @app.post("/chat")
# async def chat(request: ChatRequest, db: Session = Depends(get_db)):
#     """处理聊天请求"""
#     try:
#         print(f"收到聊天请求: user_id={request.user_id}, model={request.model}")
        
#         # 获取或创建用户
#         user = get_or_create_user(db, request.user_id)
#         print(f"用户信息: id={user.id}, user_id={user.user_id}")
        
#         # 验证模型
#         if request.model not in MODELS_CONFIG:
#             print(f"不支持的模型: {request.model}")
#             raise HTTPException(status_code=400, detail=f"不支持的模型: {request.model}")
        
#         # 获取用户历史对话
#         history = db.query(Conversation).filter(
#             Conversation.user_id == user.id
#         ).order_by(Conversation.timestamp.asc()).all()
        
#         print(f"历史对话数量: {len(history)}")
        
#         # 调用模型API
#         model_config = MODELS_CONFIG[request.model]
#         ai_reply = call_model_api(model_config, request.message, history)
        
#         # 保存对话
#         conv = Conversation(
#             user_id=user.id,
#             session_id=user.user_id,
#             user_message=request.message,
#             ai_response=ai_reply,
#             model_used=request.model
#         )
#         db.add(conv)
#         db.commit()
#         db.refresh(conv)
        
#         print(f"对话保存成功，ID: {conv.id}")
        
#         return {
#             "user_id": user.user_id,
#             "ai_reply": ai_reply,
#             "conversation_id": conv.id,
#             "model_used": request.model
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"聊天端点内部错误: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")
    
# @app.post("/rate-message")
# def rate_message(req: RatingRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == req.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="用户未找到")
    
#     conv = db.query(Conversation).filter(
#         Conversation.id == req.conversation_id,
#         Conversation.user_id == user.id
#     ).first()
    
#     if not conv:
#         raise HTTPException(status_code=404, detail="对话记录未找到")
    
#     conv.message_rating = max(1.0, min(5.0, req.rating))
#     db.commit()
#     return {"status": "ok"}

# @app.post("/rate-service")
# def rate_service(req: ServiceRatingRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == req.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="用户未找到")
    
#     convs = db.query(Conversation).filter(Conversation.user_id == user.id).all()
#     for c in convs:
#         c.service_rating = max(1.0, min(5.0, req.rating))
#     db.commit()
#     return {"status": "ok"}

# @app.get("/history/{user_id}")
# def get_history(user_id: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="用户未找到")
    
#     history = db.query(Conversation).filter(
#         Conversation.user_id == user.id
#     ).order_by(Conversation.timestamp.asc()).all()
    
#     return [{
#         "id": h.id,
#         "user": h.user_message,
#         "ai": h.ai_response,
#         "timestamp": h.timestamp.isoformat(),
#         "message_rating": h.message_rating,
#         "service_rating": h.service_rating,
#         "model_used": h.model_used
#     } for h in history]

# @app.get("/user-info/{user_id}")
# def get_user_info(user_id: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="用户未找到")
    
#     return {
#         "user_id": user.user_id,
#         "created_at": user.created_at,
#         "current_model": user.current_model,
#         "conversation_count": len(user.conversations)
#     }

# # 挂载静态文件
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

# main.py
import os
import uuid
from datetime import datetime
from typing import Optional, Dict

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from openai import OpenAI

from database import get_db, User, ChatSession, Conversation
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 FastAPI
app = FastAPI(title="智能电商购物助手")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检查 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

# 支持的模型配置
MODELS_CONFIG = {
    "qwen-doc-turbo": {
        "name": "qwen-doc-turbo",
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "system_prompt": """你是一个智能电商购物助手，请根据以下规则与用户进行多轮对话，最终推荐一个商品：
1. 目标导向：你的最终目标是推荐一个特定商品（该商品真实存在且用户曾购买过），但不要一开始就透露。
2. 知识驱动：所有提问必须基于商品的知识图谱信息，包括类别、品牌、属性（如"健康""便携""高性价比"）等实体。
3. 由粗到细：先从宽泛的类别或需求开始提问（例如："您想买饮料吗？"），再逐步聚焦到具体品牌或属性（例如："您偏好可口可乐吗？"、"需要低糖的吗？"）。
4. 问答形式：每轮只提一个问题，且必须是是非问句（Yes/No Question），例如："您喜欢健康一点的吗？"
5. 用户偏好模拟：假设用户对目标商品具备正向偏好。若问题涉及目标商品的真实属性，则用户回答"是"；否则回答"否"。
6. 自然流畅：语言要口语化、友好，避免机械重复，适时使用表情或鼓励性语句。
请开始第一轮提问。"""
    },
    "baidu/ernie-4.5-0.3b": {
        "name": "baidu/ernie-4.5-0.3b",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.ppio.com/openai",
        "system_prompt": """你是一个智能电商购物助手，请根据以下规则与用户进行多轮对话，最终推荐一个商品：
1. 目标导向：你的最终目标是推荐一个特定商品（该商品真实存在且用户曾购买过），但不要一开始就透露。
2. 知识驱动：所有提问必须基于商品的知识图谱信息，包括类别、品牌、属性（如"健康""便携""高性价比"）等实体。
3. 由粗到细：先从宽泛的类别或需求开始提问（例如："您想买饮料吗？"），再逐步聚焦到具体品牌或属性（例如："您偏好可口可乐吗？"、"需要低糖的吗？"）。
4. 问答形式：每轮只提一个问题，且必须是是非问句（Yes/No Question），例如："您喜欢健康一点的吗？"
5. 用户偏好模拟：假设用户对目标商品具备正向偏好。若问题涉及目标商品的真实属性，则用户回答"是"；否则回答"否"。
6. 自然流畅：语言要口语化、友好，避免机械重复，适时使用表情或鼓励性语句。
请开始第一轮提问。"""
    },
    "glm-4.5-flash": {
        "name": "glm-4.5-flash",
        "api_key_env": "GLM_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "system_prompt": """你是一个智能电商购物助手，请根据以下规则与用户进行多轮对话，最终推荐一个商品：
1. 目标导向：你的最终目标是推荐一个特定商品（该商品真实存在且用户曾购买过），但不要一开始就透露。
2. 知识驱动：所有提问必须基于商品的知识图谱信息，包括类别、品牌、属性（如"健康""便携""高性价比"）等实体。
3. 由粗到细：先从宽泛的类别或需求开始提问（例如："您想买饮料吗？"），再逐步聚焦到具体品牌或属性（例如："您偏好可口可乐吗？"、"需要低糖的吗？"）。
4. 问答形式：每轮只提一个问题，且必须是是非问句（Yes/No Question），例如："您喜欢健康一点的吗？"
5. 用户偏好模拟：假设用户对目标商品具备正向偏好。若问题涉及目标商品的真实属性，则用户回答"是"；否则回答"否"。
6. 自然流畅：语言要口语化、友好，避免机械重复，适时使用表情或鼓励性语句。
请开始第一轮提问。"""
    }
    
}

# 请求模型
class ChatRequest(BaseModel):
    session_id: str  # 会话ID（必需）
    message: str
    model: str = "qwen-doc-turbo"

class NewSessionRequest(BaseModel):
    user_id: Optional[str] = None
    model: str = "qwen-doc-turbo"

class RatingRequest(BaseModel):
    session_id: str
    conversation_id: int
    rating: float

def get_or_create_user(db: Session, user_id: Optional[str] = None):
    """获取或创建用户"""
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            return user
    
    new_user_id = user_id or str(uuid.uuid4())
    user = User(user_id=new_user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_active_session(db: Session, session_id: str):
    """获取活跃的会话"""
    return db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.is_active == True
    ).first()

def call_model_api(model_config: Dict, message: str, history: list = None) -> str:
    """调用大模型API"""
    api_key = os.getenv(model_config["api_key_env"])
    if not api_key:
        raise ValueError(f"请设置环境变量 {model_config['api_key_env']}")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=model_config["base_url"],
        )
        
        messages = [
            {"role": "system", "content": model_config["system_prompt"]}
        ]
        
        if history:
            for h in history:
                messages.append({"role": "user", "content": h.user_message})
                messages.append({"role": "assistant", "content": h.ai_response})
        
        messages.append({"role": "user", "content": message})
        
        completion = client.chat.completions.create(
            model=model_config["name"],
            messages=messages,
            timeout=30.0
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"API调用错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"模型错误: {str(e)}")

@app.post("/create-session")
def create_session(req: NewSessionRequest, db: Session = Depends(get_db)):
    """创建新的聊天会话"""
    user = get_or_create_user(db, req.user_id)
    
    # 检查模型是否支持
    if req.model not in MODELS_CONFIG:
        raise HTTPException(status_code=400, detail="不支持的模型")
    
    # 创建新会话
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=user.id,
        model_used=req.model
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "user_id": user.user_id,
        "session_id": session.session_id,
        "model_used": session.model_used,
        "start_time": session.start_time
    }

@app.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """处理聊天请求"""
    try:
        # 获取会话
        session = get_active_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或已结束")
        
        # 验证模型
        if request.model not in MODELS_CONFIG:
            raise HTTPException(status_code=400, detail="不支持的模型")
        
        # 获取当前会话的历史对话
        conversations = db.query(Conversation).filter(
            Conversation.session_id == session.id
        ).order_by(Conversation.turn_number.asc()).all()
        
        # 计算下一轮次
        next_turn = len(conversations) + 1
        
        # 调用模型API
        model_config = MODELS_CONFIG[request.model]
        ai_reply = call_model_api(model_config, request.message, conversations)
        
        # 保存对话记录
        conv = Conversation(
            session_id=session.id,
            turn_number=next_turn,
            user_message=request.message,
            ai_response=ai_reply
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        
        return {
            "session_id": session.session_id,
            "turn_number": next_turn,
            "ai_reply": ai_reply,
            "conversation_id": conv.id,
            "model_used": request.model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"聊天端点内部错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.post("/end-session/{session_id}")
def end_session(session_id: str, db: Session = Depends(get_db)):
    """结束指定会话"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")
    
    if not session.is_active:
        raise HTTPException(status_code=400, detail="会话已结束")
    
    session.is_active = False
    session.end_time = datetime.utcnow()
    db.commit()
    
    return {
        "status": "ok",
        "session_id": session_id,
        "end_time": session.end_time,
        "total_turns": len(session.conversations)
    }

# @app.get("/session-history/{session_id}")
# def get_session_history(session_id: str, db: Session = Depends(get_db)):
#     """获取指定会话的所有对话记录"""
#     session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
#     if not session:
#         raise HTTPException(status_code=404, detail="会话未找到")
    
#     conversations = db.query(Conversation).filter(
#         Conversation.session_id == session.id
#     ).order_by(Conversation.turn_number.asc()).all()
    
#     return {
#         "session_id": session_id,
#         "user_id": session.user.user_id,
#         "model_used": session.model_used,
#         "start_time": session.start_time,
#         "end_time": session.end_time,
#         "is_active": session.is_active,
#         "conversations": [{
#             "id": c.id,
#             "turn_number": c.turn_number,
#             "user_message": c.user_message,
#             "ai_response": c.ai_response,
#             "timestamp": c.timestamp.isoformat(),
#             "message_rating": c.message_rating
#         } for c in conversations]
#     }

@app.get("/user-sessions/{user_id}")
def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    """获取用户的所有会话"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")
    
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user.id
    ).order_by(ChatSession.start_time.desc()).all()
    
    return [{
        "session_id": s.session_id,
        "model_used": s.model_used,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "is_active": s.is_active,
        "conversation_count": len(s.conversations)
    } for s in sessions]

@app.post("/rate-message")
def rate_message(req: RatingRequest, db: Session = Depends(get_db)):
    """为单条对话评分"""
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话记录未找到")
    
    # 验证会话ID
    session = db.query(ChatSession).filter(
        ChatSession.id == conv.session_id,
        ChatSession.session_id == req.session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")
    
    conv.message_rating = max(1.0, min(5.0, req.rating))
    db.commit()
    return {"status": "ok"}

@app.get("/available-models")
def get_available_models():
    """获取可用的模型列表"""
    return {
        "models": [
            {
                "id": model_id,
                "name": config["name"],
                "description": f"{config['name']} 模型"
            }
            for model_id, config in MODELS_CONFIG.items()
        ]
    }

# 挂载静态文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================
# 数据导出功能
# ==============================

from fastapi.responses import StreamingResponse, FileResponse
import pandas as pd
from io import BytesIO, StringIO
import zipfile
import json
# 在文件顶部添加导入
from sqlalchemy import func, distinct
from datetime import timedelta

class ExportRequest(BaseModel):
    """导出请求模型"""
    format: str = "excel"  # excel, csv, json
    include_users: bool = True
    include_sessions: bool = True
    include_conversations: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.post("/export/data")
async def export_data(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    导出数据为Excel/CSV/JSON格式
    支持按时间范围筛选
    """
    try:
        # 基础查询
        base_conditions = []
        
        # 添加时间范围筛选
        if request.start_date:
            base_conditions.append(ChatSession.start_time >= request.start_date)
        if request.end_date:
            base_conditions.append(ChatSession.start_time <= request.end_date)
        
        # 1. 导出用户数据
        users_data = []
        if request.include_users:
            users_query = db.query(User)
            users = users_query.all()
            users_data = [{
                "用户ID": user.user_id,
                "创建时间": user.created_at,
                "会话数量": len(user.sessions)
            } for user in users]
        
        # 2. 导出会话数据
        sessions_data = []
        if request.include_sessions:
            sessions_query = db.query(ChatSession)
            if base_conditions:
                for condition in base_conditions:
                    sessions_query = sessions_query.filter(condition)
            
            sessions = sessions_query.order_by(ChatSession.start_time.desc()).all()
            sessions_data = [{
                "会话ID": session.session_id,
                "用户ID": session.user.user_id if session.user else None,
                "使用模型": session.model_used,
                "开始时间": session.start_time,
                "结束时间": session.end_time,
                "是否活跃": "是" if session.is_active else "否",
                "对话轮数": len(session.conversations)
            } for session in sessions]
        
        # 3. 导出对话数据
        conversations_data = []
        if request.include_conversations:
            conv_query = db.query(Conversation).join(ChatSession)
            if base_conditions:
                for condition in base_conditions:
                    conv_query = conv_query.filter(condition)
            
            conversations = conv_query.order_by(Conversation.timestamp).all()
            conversations_data = [{
                "会话ID": conv.session.session_id if conv.session else None,
                "轮次": conv.turn_number,
                "用户提问": conv.user_message,
                "AI回复": conv.ai_response,
                "时间": conv.timestamp,
                "消息评分": conv.message_rating
            } for conv in conversations]
        
        # 根据格式返回数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "json":
            # 返回JSON格式
            export_json = {
                "export_time": datetime.now().isoformat(),
                "statistics": {
                    "users": len(users_data),
                    "sessions": len(sessions_data),
                    "conversations": len(conversations_data)
                },
                "data": {
                    "users": users_data,
                    "sessions": sessions_data,
                    "conversations": conversations_data
                }
            }
            
            json_str = json.dumps(export_json, ensure_ascii=False, default=str, indent=2)
            return StreamingResponse(
                StringIO(json_str),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=export_{timestamp}.json"
                }
            )
        
        elif request.format == "csv":
            # 创建ZIP文件包含多个CSV
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if users_data:
                    users_df = pd.DataFrame(users_data)
                    users_csv = users_df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f"users_{timestamp}.csv", users_csv)
                
                if sessions_data:
                    sessions_df = pd.DataFrame(sessions_data)
                    sessions_csv = sessions_df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f"sessions_{timestamp}.csv", sessions_csv)
                
                if conversations_data:
                    convs_df = pd.DataFrame(conversations_data)
                    convs_csv = convs_df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f"conversations_{timestamp}.csv", convs_csv)
            
            zip_buffer.seek(0)
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=export_{timestamp}.zip"
                }
            )
        
        else:  # excel (默认)
            # 创建Excel文件
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                if users_data:
                    pd.DataFrame(users_data).to_excel(
                        writer, sheet_name='用户', index=False
                    )
                
                if sessions_data:
                    pd.DataFrame(sessions_data).to_excel(
                        writer, sheet_name='会话', index=False
                    )
                
                if conversations_data:
                    pd.DataFrame(conversations_data).to_excel(
                        writer, sheet_name='对话', index=False
                    )
            
            excel_buffer.seek(0)
            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=export_{timestamp}.xlsx"
                }
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/export/quick")
async def quick_export(
    format: str = "excel",
    db: Session = Depends(get_db)
):
    """
    快速导出 - 所有数据
    """
    request = ExportRequest(
        format=format,
        include_users=True,
        include_sessions=True,
        include_conversations=True
    )
    return await export_data(request, db)

@app.get("/export/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    获取统计信息
    """
    try:
        # 基础统计
        total_users = db.query(User).count()
        total_sessions = db.query(ChatSession).count()
        total_conversations = db.query(Conversation).count()
        active_sessions = db.query(ChatSession).filter(ChatSession.is_active == True).count()
        
        # 按模型统计
        model_stats = db.query(
            ChatSession.model_used,
            func.count(ChatSession.id).label('count')
        ).group_by(ChatSession.model_used).all()
        
        # 每日新增统计（最近7天）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = db.query(
            func.date(ChatSession.start_time).label('date'),
            func.count(ChatSession.id).label('sessions'),
            func.count(distinct(ChatSession.user_id)).label('users')
        ).filter(
            ChatSession.start_time >= seven_days_ago
        ).group_by(
            func.date(ChatSession.start_time)
        ).order_by(
            func.date(ChatSession.start_time).desc()
        ).all()
        
        # 评分统计
        rating_stats = db.query(
            func.avg(Conversation.message_rating).label('avg_rating'),
            func.count(Conversation.id).label('rated_count')
        ).filter(
            Conversation.message_rating.isnot(None)
        ).first()
        
        return {
            "summary": {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_conversations": total_conversations,
                "active_sessions": active_sessions
            },
            "model_usage": [
                {"model": model, "count": count}
                for model, count in model_stats
            ],
            "daily_stats": [
                {
                    "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                    "sessions": sessions,
                    "users": users
                }
                for date, sessions, users in daily_stats
            ],
            "rating_stats": {
                "average_rating": float(rating_stats.avg_rating) if rating_stats.avg_rating else 0,
                "rated_messages": rating_stats.rated_count or 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
# ==============================
# 管理员访问路由
# ==============================

@app.get("/admin")
async def admin_page():
    """返回管理员页面"""
    return FileResponse("admin.html")

# 可选：添加简单的身份验证
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@app.get("/admin/login")
async def admin_login(password: str):
    """简单的管理员登录验证"""
    if not ADMIN_PASSWORD:
        return {"message": "管理员功能未配置"}
    
    if password == ADMIN_PASSWORD:
        return {"status": "success", "token": "admin_token"}
    else:
        raise HTTPException(status_code=401, detail="密码错误")


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")


print("✅ 服务已启动，使用会话管理逻辑")


