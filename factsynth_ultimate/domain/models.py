from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class ClaimStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class Claim(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ClaimStatus = Field(default=ClaimStatus.pending)
    verdict: str | None = None
    score: float | None = None
    links: list["ClaimSourceLink"] = Relationship(back_populates="claim")


class Source(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str
    title: str | None = None
    snippet: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    links: list["ClaimSourceLink"] = Relationship(back_populates="source")


class ClaimSourceLink(SQLModel, table=True):
    claim_id: int = Field(foreign_key="claim.id", primary_key=True)
    source_id: int = Field(foreign_key="source.id", primary_key=True)
    relevance: float | None = None
    claim: Claim = Relationship(back_populates="links")
    source: Source = Relationship(back_populates="links")
