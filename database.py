# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'chat_logs_new1.db')}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    session_id = Column(String, unique=True, index=True)  # 会话唯一ID
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
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True)
    turn_number = Column(Integer)  # 对话轮次（第几轮问答）
    user_message = Column(Text)
    ai_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_rating = Column(Float, nullable=True)
    
    session = relationship("ChatSession", back_populates="conversations")

# 创建所有表
Base.metadata.create_all(bind=engine)

print("✅ 数据库表已创建")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()