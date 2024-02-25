from datetime import datetime
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Tuple
from models import Base, User, Response, UserStatusEnum

class DB_Exception(Exception):
    pass

class DB_API:
    def __init__(self):
        db_username = os.getenv('POSTGRES_USERNAME')
        if not db_username:
            raise DB_Exception('DB username not set in .env')
        
        db_password = os.getenv('POSTGRES_PASSWORD')
        if not db_password:
            raise DB_Exception('DB password not set in .env')
        
        db_host = os.getenv('POSTGRES_HOST')
        if not db_host:
            raise DB_Exception('DB host not set in .env')
        
        db_name = os.getenv('POSTGRES_DB')
        if not db_name:
            raise DB_Exception('DB name not set in .env')
        
        self.conn_string = f'postgresql+asyncpg://{db_username}:{db_password}@{db_host}/{db_name}'
        self.engine = create_async_engine(self.conn_string, echo=True)

    def _async_session_generator(self) -> sessionmaker[AsyncSession]:
        return sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    @asynccontextmanager
    async def _get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        try:
            async_session = self._async_session_generator()

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with async_session() as session:
                yield session
        except Exception as e:
            print(e)
            await session.rollback()
            raise
        finally:
            await session.close()

    async def add_user(self, tg_id: int) -> User:
        async with self._get_session() as session:
            new_user = User(tg_id)
            session.add(new_user)
            await session.commit()
            return new_user

    async def get_users(self) -> List[User]:
        async with self._get_session() as session:
            q = select(User)
            res = (await session.execute(q)).scalars().all()
            return res
        
    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        async with self._get_session() as session:
            q = select(User).where(User.telegram_id == tg_id)
            res = (await session.execute(q)).scalars().first()
            return res

    async def get_ready_users(self) -> List[Tuple[User, str]]:
        async with self._get_session() as session:
            q = select(Response)
            responses = (await session.execute(q)).scalars().all()
            res = []

            for resp in responses:
                for user in resp.users:
                    if user.status == UserStatusEnum.ALIVE and (datetime.now() - user.last_response_time).total_seconds() >= resp.time_before_send:
                        res.append((user, resp.text))

            return res

    async def set_user_status(self, tg_id: int, status: UserStatusEnum):
        async with self._get_session() as session:
            user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalars().first()
            user.status = status
            user.status_updated_at = datetime.now()
            await session.commit()

    async def set_user_next_question(self, tg_id: int):
        async with self._get_session() as session:
            user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalars().first()
            user.last_response_time = datetime.now()
            resp = await self.get_message(user.next_response.id + 1)
            print(resp.text, user)
            if resp:
                user.next_response = resp
                user.next_response_id += 1
            else:
                user.next_response = None
                user.next_response_id = None
                await self.set_user_status(tg_id, UserStatusEnum.FINISHED)
            
            await session.commit()

    async def get_messages(self) -> List[Response]:
        async with self._get_session() as session:
            q = select(Response)
            res = (await session.execute(q)).scalars().all()
            return res

    async def get_message(self, id: int) -> Response | None:
        async with self._get_session() as session:
            q = select(Response).where(Response.id == id)
            res = (await session.execute(q)).scalars().first()
            return res

    async def add_default_messages(self):
        async with self._get_session() as session:
            q = select(Response)
            res = (await session.execute(q)).scalars().all()

            if res:
                return

            msg_1 = Response('msg_1', time_before_send=6 * 60)
            msg_2 = Response('msg_2', ['триггер1'], time_before_send=39 * 60)
            msg_3 = Response('msg_3', time_before_send=26*60*60)
        
            session.add(msg_1)
            session.add(msg_2)
            session.add(msg_3)
            await session.commit()
