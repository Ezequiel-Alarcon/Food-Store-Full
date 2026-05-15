from datetime import datetime,timezone
from sqlmodel import SQLModel, Field
from typing import Optional

class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at: Optional[datetime] = Field(
        default=None, 
        nullable=True
    )
    borrado: bool = Field(default=False)