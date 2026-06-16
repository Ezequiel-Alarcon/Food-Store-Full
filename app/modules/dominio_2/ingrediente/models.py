from typing import TYPE_CHECKING, ClassVar, Optional, List
from sqlmodel import Field, Relationship
from ..producto.models import ProductoIngrediente
from app.core.minxins.auditable_mixin import UniqueAuditableMixin
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from ..producto.models import Producto
    from ..UnidadMedida.models import UnidadMedida

class Ingrediente(UniqueAuditableMixin, SQLModel, table=True):
    __tablename__ = "ingredientes"

    _unique_fields: ClassVar[List[str]] = ["nombre"]

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(..., description="Nombre del ingrediente")
    es_alergeno: bool = Field(default=False, description="Indica si el ingrediente es un alérgeno")
    descripcion: str | None = Field(default=None, description="Descripción del ingrediente")

    unidad_medida_id: int = Field(foreign_key="unidades_medida.id") 
    
    unidad_medida: "UnidadMedida" = Relationship()
    
    # Relación con productos a través de la tabla intermedia
    productos: list["Producto"] = Relationship(
        back_populates="ingredientes",
        link_model=ProductoIngrediente
    )