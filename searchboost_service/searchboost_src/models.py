from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from searchboost_src.database import Base

class SearchResult(Base):
    __tablename__ = "search_results"

    job_id = Column(String, primary_key=True)
    query = Column(String, nullable=False)
    final_answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)