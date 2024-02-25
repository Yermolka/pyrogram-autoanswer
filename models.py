from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    UUID,
    ARRAY,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime
import enum
from typing import List

def generate_uuid():
    return uuid.uuid4()

Base = declarative_base()

class Response(Base):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(200))
    cancel_triggers = Column(ARRAY(String), nullable=True)
    time_before_send = Column(Integer) # In seconds

    users = relationship('User', back_populates='next_response', lazy='selectin')

    def __init__(self, text: str, cancel_triggers: List[str] = None, time_before_send: int = 60):
        self.text = text
        self.cancel_triggers = cancel_triggers
        self.time_before_send = time_before_send

    def __str__(self) -> str:
        return f'{self.id}: {self.text}'

class UserStatusEnum(enum.Enum):
    ALIVE = 1
    DEAD = 2
    FINISHED = 3

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True, default=generate_uuid)
    telegram_id = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.ALIVE)
    status_updated_at = Column(DateTime, default=datetime.now)

    next_response_id = Column(ForeignKey(Response.id), nullable=True)
    next_response = relationship('Response', lazy='immediate')
    last_response_time = Column(DateTime, default=datetime.now)

    def __init__(self, tg_id: str):
        self.telegram_id = tg_id
        self.next_response_id = 1

    def __str__(self) -> str:
        return f'{self.telegram_id}: {self.status}'