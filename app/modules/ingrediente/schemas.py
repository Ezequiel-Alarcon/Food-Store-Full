from typing import Optional
from sqlmodel import SQLModel, Field


# Esquema reducido local para evitar dependencia circular
class ProductoBasicRead(SQLModel):
    id: int
    nombre: str
# ─── Base ─────────────────────────────────────────────────────────────────────────────────


class IngredienteBase(SQLModel):
    nombre: str = Field(..., description="Nombre del ingrediente")
    es_alergeno: bool = Field(
        default=False, description="Indica si el ingrediente es un alérgeno")
    descripcion: Optional[str] = Field(default=None, description="Descripción del ingrediente")


# ─── Request schemas ──────────────────────────────────────────────────────────────────────


class IngredienteCreate(IngredienteBase):
    pass


class IngredienteUpdate(SQLModel):
    nombre: Optional[str] = Field(
        default=None, description="Nombre del ingrediente")
    es_alergeno: Optional[bool] = Field(
        default=None, description="Indica si el ingrediente es un alérgeno")
    descripcion: Optional[str] = Field(
        default=None, description="Descripción del ingrediente")


# ─── Response schemas ────────────────────────────────────────────────────────────────────

class IngredienteRead(IngredienteBase):
    id: int = Field(..., description="ID del ingrediente")


class IngredienteBasicRead(SQLModel):
    id: int = Field(..., description="ID del ingrediente")
    nombre: str = Field(..., description="Nombre del ingrediente")


class IngredienteReadFull(IngredienteRead):
    productos: list[ProductoBasicRead] = Field(
        default_factory=list, description="Lista de productos")


class IngredienteList(SQLModel):
    data: list[IngredienteReadFull]
    total: int
