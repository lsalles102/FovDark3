from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    data_expiracao = Column(DateTime, nullable=True)  # Data de expiração da licença
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com pagamentos
    payments = relationship("Payment", back_populates="user")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    valor = Column(Float, nullable=False)
    data_pagamento = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  # completed, pending, failed
    plano = Column(String, nullable=True)  # mensal, trimestral, anual
    gateway_id = Column(String, nullable=True)  # ID do gateway de pagamento
    
    # Relacionamento com usuário
    user = relationship("User", back_populates="payments")


class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # create, update, delete, etc.
    target_table = Column(String, nullable=False)  # users, payments, etc.
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON com detalhes da ação
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com admin
    admin = relationship("User")
