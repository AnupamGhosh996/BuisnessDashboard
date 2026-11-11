import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    report_type = Column(String(100), nullable=False)  # 'executive_summary', 'monthly_sales', 'revenue_analysis', etc.
    title = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_format = Column(String(50), default="pdf")  # 'pdf', 'xlsx', 'csv'
    summary_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="reports")
