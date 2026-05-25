from fastapi import HTTPException
from typing import Optional, cast

from app.core.enums import EstadoFiltro
from app.modules.dominio_2.producto.models import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.dominio_2.producto.schemas import (
    CategoriaBasicRead,
    IngredienteBasicRead,
    ProductoCreate,
    ProductoReadFull,
    ProductoUpdate,
)

from app.modules.dominio_2.producto.unit_of_work import ProductoUnitOfWork

class ProductoService:
    def __init__(self, uow: ProductoUnitOfWork) -> None:
            self._uow = uow

    # ── Helpers privados ─────────────────────────────────────────────────────
    def _get_or_404(self, uow: ProductoUnitOfWork, producto_id: int) -> Producto:
        producto = uow.productos.get_by_id(producto_id)
        if not producto:
            raise HTTPException(
                status_code=404,
                detail=f"Producto con ID {producto_id} no encontrado"
            )
        return producto
    
    def _validar_nombre_unico(self, uow: ProductoUnitOfWork, name: str) -> None:
        producto = uow.productos.get_by_name(name)
        if producto:
            raise HTTPException(
                status_code=400,
                detail=f"El nombre '{name}' ya está en uso por otro producto"
            )

    def _to_read_full(self, uow: ProductoUnitOfWork, producto: Producto) -> ProductoReadFull:
        categoria_links = uow.producto_categorias.list_by_producto(cast(int, producto.id))
        categoria_principal_por_id = {
            link.categoria_id: link.es_principal
            for link in categoria_links
        }

        categorias = [
            CategoriaBasicRead(
                id=cast(int, categoria.id),
                nombre=categoria.nombre,
                es_principal=categoria_principal_por_id.get(cast(int, categoria.id), False),
            )
            for categoria in producto.categorias
            if categoria.deleted_at is None
        ]
        ingredientes = [
            IngredienteBasicRead(
                id=cast(int, ingrediente.id),
                nombre=ingrediente.nombre,
                es_alergeno=ingrediente.es_alergeno,
            )
            for ingrediente in producto.ingredientes
            if ingrediente.deleted_at is None
        ]
        return ProductoReadFull(
            id=cast(int, producto.id),
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio_base=producto.precio_base,
            imagenes_url=producto.imagenes_url,
            stock_cantidad=producto.stock_cantidad,
            disponible=producto.disponible,
            categorias=categorias,
            ingredientes=ingredientes,
        )

    # ── Métodos públicos ───────────────────────────────────────────────────

    def create(self, data: ProductoCreate) -> ProductoReadFull:
        with self._uow as uow:
            self._validar_nombre_unico(uow, data.nombre)
            
            # Excluimos las relaciones porque no van en la tabla "productos" directamente
            data_dict = data.model_dump(exclude={"categoria_ids", "ingrediente_ids"})
            nuevo_producto = Producto(**data_dict)
            uow.productos.add(nuevo_producto)
            
            # 1. Asignar categorías (la primera será la principal)
            for i, cat_id in enumerate(data.categoria_ids):
                cat = uow.categorias.get_by_id(cat_id)
                if not cat:
                    raise HTTPException(status_code=404, detail=f"Categoría con ID {cat_id} no encontrada")
                
                link = ProductoCategoria(
                    producto_id=cast(int, nuevo_producto.id),
                    categoria_id=cat_id,
                    es_principal=(i == 0) # La posición 0 es la principal
                )
                uow.producto_categorias.create(link)
                
            # 2. Asignar ingredientes si vinieron
            if data.ingrediente_ids:
                for ing_id in data.ingrediente_ids:
                    ing = uow.ingredientes.get_by_id(ing_id)
                    if not ing:
                        raise HTTPException(status_code=404, detail=f"Ingrediente con ID {ing_id} no encontrado")
                    
                    link_ing = ProductoIngrediente(
                        producto_id=cast(int, nuevo_producto.id),
                        ingrediente_id=ing_id
                    )
                    uow.producto_ingredientes.create(link_ing)
                    
            return self._to_read_full(uow, nuevo_producto)

    def get_all(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            productos = uow.productos.get_all_by_state(EstadoFiltro.ACTIVO, offset, limit)
            total = uow.productos.count_model(EstadoFiltro.ACTIVO)
            resultado = {"data": [self._to_read_full(uow, p) for p in productos], "total": total}
            return resultado
    
    def get_active(
        self,
        offset: int = 0,
        limit: int = 20,
        categoria_ids: Optional[list[int]] = None,
        ingrediente_ids: Optional[list[int]] = None,
    ):
        with self._uow as uow:
            productos = uow.productos.get_active(
                offset, limit,
                categoria_ids=categoria_ids,
                ingrediente_ids=ingrediente_ids,
            )
            total = uow.productos.count_active(
                categoria_ids=categoria_ids,
                ingrediente_ids=ingrediente_ids,
            )
            resultado = {"data": [self._to_read_full(uow, p) for p in productos], "total": total}
            return resultado
    
    def get_by_category(self, categoria_id: int, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            categoria = uow.categorias.get_by_id(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=404,
                    detail=f"Categoría con ID {categoria_id} no encontrada"
                )
            productos = uow.productos.get_by_category(categoria_id, offset, limit)
            total = uow.productos.count_by_category(categoria_id)
            resultado = {"data": [self._to_read_full(uow, p) for p in productos], "total": total}
            return resultado
    
    def get_by_id(self, producto_id: int) -> ProductoReadFull:
        with self._uow as uow:
            producto = self._get_or_404(uow, producto_id)
            return self._to_read_full(uow, producto)
    
    def update(self, producto_id: int, data: ProductoUpdate) -> ProductoReadFull:
        with self._uow as uow:
            producto = self._get_or_404(uow, producto_id)
            patch = data.model_dump(exclude_unset=True, exclude={"categoria_ids", "ingrediente_ids"})

            if "nombre" in patch and patch["nombre"] != producto.nombre:
                existente = uow.productos.get_by_name(patch["nombre"])
                if existente and existente.id != producto_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El nombre '{patch['nombre']}' ya está en uso por otro producto"
                    )

            for field, value in patch.items():
                setattr(producto, field, value)
                
            # Si se enviaron categorías para actualizar
            if data.categoria_ids is not None:
                # Limpiar las viejas
                viejas_cats = uow.producto_categorias.list_by_producto(producto_id)
                for vc in viejas_cats:
                    uow.producto_categorias.delete(vc)
                # Crear las nuevas
                for i, cat_id in enumerate(data.categoria_ids):
                    cat = uow.categorias.get_by_id(cat_id)
                    if not cat:
                        raise HTTPException(status_code=404, detail=f"Categoría con ID {cat_id} no encontrada")
                    link = ProductoCategoria(
                        producto_id=producto_id,
                        categoria_id=cat_id,
                        es_principal=(i == 0)
                    )
                    uow.producto_categorias.create(link)
                    
            # Si se enviaron ingredientes para actualizar
            if data.ingrediente_ids is not None:
                # Limpiar los viejos
                viejos_ings = uow.producto_ingredientes.list_by_producto(producto_id)
                for vi in viejos_ings:
                    uow.producto_ingredientes.delete(vi)
                # Crear los nuevos
                for ing_id in data.ingrediente_ids:
                    ing = uow.ingredientes.get_by_id(ing_id)
                    if not ing:
                        raise HTTPException(status_code=404, detail=f"Ingrediente con ID {ing_id} no encontrado")
                    link_ing = ProductoIngrediente(
                        producto_id=producto_id,
                        ingrediente_id=ing_id
                    )
                    uow.producto_ingredientes.create(link_ing)

            uow.productos.update(producto)
            return self._to_read_full(uow, producto)

    def delete(self, producto_id: int) -> None:
        with self._uow as uow:
            producto = self._get_or_404(uow, producto_id)
            uow.productos.delete(producto)
