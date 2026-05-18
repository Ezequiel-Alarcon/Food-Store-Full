from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from pydantic import field_validator
from ..base.models import BaseModel
from sqlmodel import Field, Relationship, Column, Integer, ForeignKey, SQLModel, ARRAY, String
from sqlalchemy import CheckConstraint, Numeric


if TYPE_CHECKING:
    from ..categoria.models import Categoria
    from ..ingrediente.models import Ingrediente


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"
    
    # La combinación de producto_id y categoria_id para evitar duplicados de relacion
    producto_id: int = Field(
        sa_column=Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"),  #borra relaciones si se borra el producto
        primary_key=True, nullable=False)
    )
    categoria_id: int = Field(
        sa_column=Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), #no permite borrar categoria si tiene productos relacionados
        primary_key=True, nullable=False)
    )
    es_principal: bool = Field(default=False, description="Indica si es categoría principal del producto")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"
    
    producto_id: int = Field(
        sa_column=Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), 
        primary_key=True, nullable=False)
    )
    ingrediente_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ingredientes.id", ondelete="RESTRICT"), 
        primary_key=True, nullable=False)
    )
    es_removible: bool = Field(default=False, description="Indica si el ingrediente es removible")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class Producto(BaseModel, table=True):
    __tablename__ = "productos"

    # Constraint a nivel de BD: última línea de defensa
    __table_args__ = (
        CheckConstraint("precio_base >= 0", name="ck_producto_precio_no_negativo"),
    )

    #no puede ser nulo
    nombre: str = Field(..., description="Nombre del producto", max_length=150)
    descripcion: Optional[str] = Field(default=None, description="Descripción del producto")
    #no puede ser nulo y checar que sea mayor o igual a 0
    precio_base: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
        description="Precio base del producto"
    )
    imagenes_url: Optional[list[str]] = Field(default=None, sa_column=Column(ARRAY(String)))    
    stock_cantidad: int = Field(default=0, ge=0, description="Cantidad en stock")
    disponible: bool = Field(default=True, description="Si el producto está disponible para venta")
    
    # ── Validador de dominio (capa Python) ────────────────────────────────
    @field_validator("precio_base")
    @classmethod
    def precio_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El precio base no puede ser negativo")
        return v

    # Relaciones N:N Bidireccional
    categorias: list["Categoria"] = Relationship(
        back_populates="productos",
        link_model=ProductoCategoria
    )
    ingredientes: list["Ingrediente"] = Relationship(
        back_populates="productos",
        link_model=ProductoIngrediente
    )
