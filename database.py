# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# ==============================
# 自动选择数据库：SQLite（本地） 或 PostgreSQL（Railway/云）
# ==============================

# 优先从环境变量读取 DATABASE_URL（Railway 会自动注入）
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # 🌐 云环境：使用 PostgreSQL
    # 注意：PostgreSQL 要求外键类型一致，session_id 在 ChatSession 是 String，但 Conversation 中引用的是 id (Integer)
    # 所以 Conversation.session_id 应为 Integer（你原设计正确）
    engine = create_engine(DATABASE_URL)
else:
    # 💻 本地开发：使用 SQLite
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLITE_DB_PATH = os.path.join(BASE_DIR, "chat_logs_new1.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


# ==============================
# 数据模型定义（保持你的原有结构）
# ==============================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # 用户唯一ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    """聊天会话表 - 每个完整的对话为一个会话"""
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # 会话唯一ID（前端传入）
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    model_used = Column(String)  # 该会话使用的模型
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)  # 是否活跃
    
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")


class Conversation(Base):
    """对话记录表 - 每次问答对为一条记录"""
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True)  # 引用 ChatSession.id（Integer）
    turn_number = Column(Integer)  # 对话轮次（第几轮问答）
    user_message = Column(Text)
    ai_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_rating = Column(Float, nullable=True)
    
    session = relationship("ChatSession", back_populates="conversations")


# ==============================
# 创建表 & 工具函数
# ==============================

# 创建所有表（注意：在 PostgreSQL 中需确保用户有权限）
Base.metadata.create_all(bind=engine)

print("✅ 数据库表已创建（SQLite 或 PostgreSQL）")


def get_db():
    """FastAPI 依赖项：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
