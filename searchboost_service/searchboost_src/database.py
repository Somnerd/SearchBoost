from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from searchboost_src.configurator import PostgreSQLSettings

Base = declarative_base()

engine = create_async_engine(PostgreSQLSettings.database_url(), pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Initializes tables in Postgres."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)