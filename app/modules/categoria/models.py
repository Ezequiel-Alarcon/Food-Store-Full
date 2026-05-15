from typing import TYPE_CHECKING, Optional

from app.modules.producto.models import ProductoCategoria
from ..base.models import BaseModel
from sqlmodel import Field, Relationship

# Evitar las importaciones circulares
if TYPE_CHECKING:
    from ..producto.models import Producto


class Categoria(BaseModel, table=True):
    __tablename__ = "categorias"
    
    parent_id: int | None = Field(
        default=None,
        foreign_key="categorias.id",
        description="FK a categoría padre"
    )
    
    nombre: str = Field(..., unique=True, max_length=100, description="Nombre de la categoría")
    
    descripcion: str | None = Field(default=None, description="Descripción")
    
    imagen_url: str = Field(..., description="URL de imagen de la categoría")

    parent: Optional["Categoria"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Categoria.id"}
    )
    
    children: list["Categoria"] = Relationship(
        back_populates="parent"
    )

    # Relación con productos a través de la tabla intermedia
    productos: list["Producto"] = Relationship(
        back_populates="categorias",
        link_model=ProductoCategoria
    )