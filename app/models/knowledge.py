import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.base import Base
from app.core.config import settings


class MaritalKnowledge(Base):
    __tablename__ = "marital_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source metadata — which law/document this chunk came from
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "MFLO 1961"
    section: Mapped[str] = mapped_column(String(255), nullable=True)  # e.g. "Section 7"

    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
