from fastapi import HTTPException
from typing import Optional, cast
from sqlmodel import Session

from app.core.cloudinary_service import eliminar_imagen, eliminar_multiples_imagenes
from app.core.enums import EstadoFiltro
from app.core.service import base_service
from app.modules.dominio_2.producto.models import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.dominio_2.producto.schemas import (
    CategoriaBasicRead,
    ProductoCreate,
    ProductoReadFull,
    ProductoUpdate,
    ProductoIngredienteRead
)
from app.modules.dominio_2.producto.unit_of_work import ProductoUnitOfWork


class ProductoService(base_service[Producto, ProductoCreate, ProductoUpdate, ProductoUnitOfWork]):
    def __init__(self, session: Session) -> None:
        super().__init__(
            session=session,
            uow_instance=ProductoUnitOfWork(session),
            repo_name="productos",
            model_class=Producto
        )

    # ── Helpers privados ─────────────────────────────────────────────────────

    def _validar_nombre_unico(self, name: str, exclude_id: Optional[int] = None) -> None:
        producto = self.repo.get_by_name(name, include_deleted=True)
        if producto and producto.id != exclude_id:
            raise HTTPException(
                status_code=400, detail=f"El nombre '{name}' ya está en uso por otro producto")

    def _to_read_full(self, producto: Producto) -> ProductoReadFull:
        categoria_links = self.uow.producto_categorias.list_by_producto(
            cast(int, producto.id))
        categoria_principal_por_id = {
            link.categoria_id: link.es_principal for link in categoria_links
        }

        categorias = [
            CategoriaBasicRead(
                id=cast(int, categoria.id),
                nombre=categoria.nombre,
                es_principal=categoria_principal_por_id.get(
                    cast(int, categoria.id), False),
            )
            for categoria in producto.categorias if getattr(categoria, "deleted_at", None) is None
        ]

        ingrediente_links = self.uow.producto_ingredientes.list_by_producto(
            cast(int, producto.id))
        es_removible_por_id = {
            link.ingrediente_id: link.es_removible for link in ingrediente_links
        }

        ingredientes = [
            ProductoIngredienteRead(
                id=cast(int, ingrediente.id),
                nombre=ingrediente.nombre,
                es_alergeno=ingrediente.es_alergeno,
                es_removible=es_removible_por_id.get(
                    cast(int, ingrediente.id), False)
            )
            for ingrediente in producto.ingredientes if getattr(ingrediente, "deleted_at", None) is None
        ]

        return ProductoReadFull(
            id=cast(int, producto.id),
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio_base=producto.precio_base,
            imagenes_url=producto.imagenes_url,
            imagenes_public_id=producto.imagenes_public_id,
            stock_cantidad=producto.stock_cantidad,
            disponible=producto.disponible,
            categorias=categorias,
            ingredientes=ingredientes,
        )

    # ── Overrides y Métodos públicos ─────────────────────────────────────────

    def get_all_productos(
        self,
        offset: int = 0,
        limit: int = 20,
        estado: EstadoFiltro = EstadoFiltro.ACTIVO,
        disponible: Optional[bool] = None,
        categoria_ids: Optional[list[int]] = None,
        ingrediente_ids: Optional[list[int]] = None,
        q: Optional[str] = None
    ):
        with self.uow:
            productos = self.repo.get_all_filtered(
                state=estado, disponible=disponible,
                categoria_ids=categoria_ids, ingrediente_ids=ingrediente_ids,
                q=q, offset=offset, limit=limit
            )
            total = self.repo.count_filtered(
                state=estado, disponible=disponible,
                categoria_ids=categoria_ids, ingrediente_ids=ingrediente_ids, q=q
            )
            return {"data": [self._to_read_full(p) for p in productos], "total": total}

    def get_by_id_full(self, producto_id: int, allow_deleted: bool = False) -> ProductoReadFull:
        with self.uow:
            producto = self._get_or_404(producto_id, allow_deleted)
            return self._to_read_full(producto)

    def create(self, data: ProductoCreate) -> ProductoReadFull:
        with self.uow:
            self._validar_nombre_unico(data.nombre)

            data_dict = data.model_dump(
                exclude={"categoria_ids", "ingredientes"})
            nuevo_producto = Producto(**data_dict)
            self.repo.add(nuevo_producto)

            for i, cat_id in enumerate(data.categoria_ids):
                cat = self.uow.categorias.get_by_id(cat_id)
                if not cat or getattr(cat, "deleted_at", None) is not None:
                    raise HTTPException(
                        status_code=404, detail=f"Categoría con ID {cat_id} no encontrada o eliminada")

                link = ProductoCategoria(
                    producto_id=cast(int, nuevo_producto.id),
                    categoria_id=cat_id,
                    es_principal=(i == 0)
                )
                self.uow.producto_categorias.add(link)

            if data.ingredientes:
                for ing_input in data.ingredientes:
                    ing = self.uow.ingredientes.get_by_id(
                        ing_input.ingrediente_id)
                    if not ing or getattr(ing, "deleted_at", None) is not None:
                        raise HTTPException(
                            status_code=404, detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado o eliminado")

                    link_ing = ProductoIngrediente(
                        producto_id=cast(int, nuevo_producto.id),
                        ingrediente_id=ing_input.ingrediente_id,
                        es_removible=ing_input.es_removible
                    )
                    self.uow.producto_ingredientes.add(link_ing)

            return self._to_read_full(nuevo_producto)

    def update(self, producto_id: int, data: ProductoUpdate) -> ProductoReadFull:
        with self.uow:
            producto = self._get_or_404(producto_id)
            # Capturamos los public_ids viejos ANTES del patch para poder
            # detectar cuáles imágenes fueron removidas del set nuevo.
            public_ids_viejos = list(producto.imagenes_public_id or [])
            patch = data.model_dump(exclude_unset=True, exclude={
                                    "categoria_ids", "ingredientes"})

            if "unidad_venta_id" in patch and patch["unidad_venta_id"] is not None:
                unidad = self.uow.unidad_medida.get_by_id(
                    patch["unidad_venta_id"])
                if not unidad:
                    raise HTTPException(
                        status_code=404, detail=f"Unidad de medida con ID {patch['unidad_venta_id']} no encontrada")

            if "nombre" in patch and patch["nombre"] != producto.nombre:
                self._validar_nombre_unico(
                    patch["nombre"], exclude_id=producto_id)

            for key, value in patch.items():
                setattr(producto, key, value)
            if hasattr(producto, "updated_at"):
                from datetime import datetime, timezone
                producto.updated_at = datetime.now(timezone.utc)
                
            self.repo.update(producto)

            if data.categoria_ids is not None:
                viejas_cats = self.uow.producto_categorias.list_by_producto(
                    producto_id)
                for vc in viejas_cats:
                    self.uow.producto_categorias.delete(vc)

                for i, cat_id in enumerate(data.categoria_ids):
                    cat = self.uow.categorias.get_by_id(cat_id)
                    if not cat or getattr(cat, "deleted_at", None) is not None:
                        raise HTTPException(
                            status_code=404, detail=f"Categoría con ID {cat_id} no encontrada")

                    link = ProductoCategoria(
                        producto_id=producto_id, categoria_id=cat_id, es_principal=(i == 0))
                    self.uow.producto_categorias.add(link)

            if data.ingredientes is not None:
                viejos_ings = self.uow.producto_ingredientes.list_by_producto(
                    producto_id)
                for vi in viejos_ings:
                    self.uow.producto_ingredientes.delete(vi)

                for ing_input in data.ingredientes:
                    ing = self.uow.ingredientes.get_by_id(
                        ing_input.ingrediente_id)
                    if not ing or getattr(ing, "deleted_at", None) is not None:
                        raise HTTPException(
                            status_code=404, detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado")

                    link_ing = ProductoIngrediente(
                        producto_id=producto_id,
                        ingrediente_id=ing_input.ingrediente_id,
                        es_removible=ing_input.es_removible
                    )
                    self.uow.producto_ingredientes.add(link_ing)

            read = self._to_read_full(producto)
            public_ids_nuevos = list(producto.imagenes_public_id or [])

        # Limpieza de Cloudinary fuera de la transacción. Si la lista de
        # public_ids cambió (se removieron imágenes, o se reemplazaron
        # todas), los public_ids viejos que ya no estén en el set nuevo
        # quedan huérfanos y se eliminan.
        if "imagenes_public_id" in patch:
            set_viejo = {pid for pid in public_ids_viejos if pid}
            set_nuevo = {pid for pid in public_ids_nuevos if pid}
            imagenes_a_borrar = set_viejo - set_nuevo
            for pid in imagenes_a_borrar:
                eliminar_imagen(pid)

        return read


    def delete(self, producto_id: int):
        with self.uow:
            producto = self._get_or_404(producto_id)
            public_ids_imagenes = list(producto.imagenes_public_id or [])
            self.repo.delete(producto)
        # Soft delete ya commiteado; eliminamos todas las imágenes del
        # producto en Cloudinary.
        eliminar_multiples_imagenes(public_ids_imagenes)
        return {"mensaje": f"Producto {producto_id} eliminado/a correctamente"}

    def toggle_disponibilidad(self, producto_id: int) -> ProductoReadFull:
        with self.uow:
            producto = self._get_or_404(producto_id)
            producto.disponible = not producto.disponible
            self.repo.update(producto)
            return self._to_read_full(producto)
