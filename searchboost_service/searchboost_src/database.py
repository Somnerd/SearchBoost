from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from searchboost_src.configurator import PostgreSQLSettings

Base = declarative_base()

class DatabaseManager:
    def __init__(self, settings: PostgreSQLSettings):
        self.settings = settings
        self.engine = create_async_engine(
            self.settings.database_url,
            pool_size=10,
            max_overflow=20
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Creates tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def get_session(self) -> AsyncSession:
        return self.session_factory()