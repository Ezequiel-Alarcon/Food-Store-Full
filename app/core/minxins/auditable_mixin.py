from typing import ClassVar, List, Optional
from datetime import datetime, timezone
from sqlmodel import Field
from sqlalchemy import Index, text
from sqlalchemy.orm import declared_attr

class UniqueAuditableMixin:
    _unique_fields: ClassVar[List[str]] = []

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    @declared_attr
    def __table_args__(cls):
        indexes = []
        tabla_nombre = cls.__tablename__
        
        for field_name in cls._unique_fields:
            idx = Index(
                f"uq_{tabla_nombre}_{field_name}_activo", 
                field_name,
                unique=True,
                postgresql_where=text("deleted_at IS NULL")
            )
            indexes.append(idx)
            
        return tuple(indexes)