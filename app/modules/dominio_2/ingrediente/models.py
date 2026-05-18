from typing import TYPE_CHECKING
from ..base.models import BaseModel
from sqlmodel import Field, Relationship
from ..producto.models import ProductoIngrediente

if TYPE_CHECKING:
    from ..producto.models import Producto

class Ingrediente(BaseModel, table=True):
    __tablename__ = "ingredientes"
    nombre: str = Field(...,unique=True, description="Nombre del ingrediente")
    es_alergeno: bool = Field(default=False, description="Indica si el ingrediente es un alérgeno")
    descripcion: str | None = Field(default=None, description="Descripción del ingrediente")
    
    # Relación con productos a través de la tabla intermedia
    productos: list["Producto"] = Relationship(
        back_populates="ingredientes",
        link_model=ProductoIngrediente
    )
