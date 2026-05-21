from typing import Optional
from pydantic import BaseModel, Field
import uuid

# --- Base ---
class DireccionBase(BaseModel):
    alias: Optional[str] = Field(default=None, max_length=50, description="Ej: Casa, Trabajo")
    linea1: str = Field(..., description="Calle y número")
    linea2: Optional[str] = Field(default=None, description="Piso, depto, etc.")
    ciudad: str = Field(..., max_length=100)
    provincia: Optional[str] = Field(default=None, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=10)

# --- Request ---
class DireccionCreate(DireccionBase):
    pass # El usuario no manda si es principal en el POST, eso va por el PATCH

class DireccionUpdate(BaseModel):
    # Todo opcional para el PATCH normal
    alias: Optional[str] = Field(default=None, max_length=50)
    linea1: Optional[str] = None
    linea2: Optional[str] = None
    ciudad: Optional[str] = Field(default=None, max_length=100)
    provincia: Optional[str] = Field(default=None, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=10)

# --- Response ---
class DireccionRead(DireccionBase):
    id: int
    usuario_id: uuid.UUID
    es_principal: bool