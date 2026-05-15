from fastapi import HTTPException
from typing import cast

from app.modules.categoria.models import Categoria
from app.modules.categoria.schemas import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaReadFull,
    ProductoBasicRead,
    CategoriaTreeList,
    CategoriaTreeNode,
    CategoriaUpdate,
)
from app.modules.categoria.unit_of_work import CategoriaUnitOfWork


class CategoriaService:
    def __init__(self, uow: CategoriaUnitOfWork) -> None:
        self._uow = uow

    # ── Helpers privados ─────────────────────────────────────────────────────
    def _get_or_404(self, uow: CategoriaUnitOfWork, categoria_id: int) -> Categoria:
        categoria = uow.categorias.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=404,
                detail=f"Categoría con ID {categoria_id} no encontrada"
            )
        return categoria

    def _validar_nombre_unico(self, uow: CategoriaUnitOfWork, name: str) -> None:
        categoria = uow.categorias.get_by_name(name, include_deleted=True)
        if categoria:
            raise HTTPException(
                status_code=400,
                detail=f"El nombre '{name}' ya está en uso por otra categoría"
            )

    def _validar_jerarquia_padre(
        self,
        uow: CategoriaUnitOfWork,
        categoria_id: int,
        parent_id: int | None
    ) -> None:
        current_parent_id = parent_id

        while current_parent_id is not None:
            if current_parent_id == categoria_id:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede generar un ciclo en el árbol de categorías"
                )

            parent = self._get_or_404(uow, current_parent_id)
            current_parent_id = parent.parent_id

    def _to_read_full(self, categoria: Categoria) -> CategoriaReadFull:
        productos = [
            ProductoBasicRead(id=cast(int, producto.id), nombre=producto.nombre)
            for producto in categoria.productos
            if not producto.borrado
        ]
        return CategoriaReadFull(
            id=cast(int, categoria.id),
            parent_id=categoria.parent_id,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
            imagen_url=categoria.imagen_url,
            productos=productos,
        )

    def _build_tree_node(self, categoria_id: int, children_by_parent: dict[int | None, list[Categoria]]) -> CategoriaTreeNode:
        categoria = next(
            child for child_list in children_by_parent.values() for child in child_list
            if child.id == categoria_id
        )
        subcategorias = [
            self._build_tree_node(cast(int, child.id), children_by_parent)
            for child in children_by_parent.get(categoria.id, [])
        ]
        return CategoriaTreeNode(
            id=cast(int, categoria.id),
            parent_id=categoria.parent_id,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
            imagen_url=categoria.imagen_url,
            subcategorias=subcategorias,
        )

    # ── Métodos públicos ───────────────────────────────────────────────────

    def create(self, data: CategoriaCreate) -> CategoriaRead:
        with self._uow as uow:
            # Validar que el nombre sea único
            self._validar_nombre_unico(uow, data.nombre)
            
            # Si se especifica un parent_id, validar que exista la categoría padre
            if data.parent_id is not None:
                self._get_or_404(uow, data.parent_id)
    
            nueva_categoria = Categoria.model_validate(data)
            uow.categorias.create(nueva_categoria)
            return CategoriaRead.model_validate(nueva_categoria)

    def get_all(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            categorias = uow.categorias.get_all(offset, limit)
            total = uow.categorias.count()
            resultado = {"data": [self._to_read_full(c) for c in categorias], "total": total}
            return resultado

    def get_principales(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            categorias = uow.categorias.get_categories(offset, limit)
            total = uow.categorias.count_principales()
            resultado = {"data": [self._to_read_full(c) for c in categorias], "total": total}
            return resultado

    def get_by_parent(self, parent_id: int, offset: int = 0, limit: int = 20):
        # Validar que exista la categoría padre
        with self._uow as uow:
            self._get_or_404(uow, parent_id)
            categorias = uow.categorias.get_by_parent(parent_id, offset, limit)
            total = uow.categorias.count_subcategories(parent_id)
            resultado = {"data": [self._to_read_full(c) for c in categorias], "total": total}
            return resultado

    def get_by_id(self, categoria_id: int) -> CategoriaReadFull:
        with self._uow as uow:
            categoria = self._get_or_404(uow, categoria_id)
            return self._to_read_full(categoria)

    def get_ordenadas(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            categorias = uow.categorias.get_ordenadas(offset, limit)
            total = uow.categorias.count()
            resultado = {"data": [self._to_read_full(c) for c in categorias], "total": total}
            return resultado

    def get_tree(self) -> CategoriaTreeList:
        with self._uow as uow:
            categorias = uow.categorias.get_all_ordered()
            children_by_parent: dict[int | None, list[Categoria]] = {}

            for categoria in categorias:
                children_by_parent.setdefault(categoria.parent_id, []).append(categoria)

            data = [
                self._build_tree_node(cast(int, root.id), children_by_parent)
                for root in children_by_parent.get(None, [])
            ]
            return CategoriaTreeList(data=data, total=len(data))

    def update(self, categoria_id: int, data: CategoriaUpdate) -> CategoriaRead:
        with self._uow as uow:
            categoria = self._get_or_404(uow, categoria_id)
            patch = data.model_dump(exclude_unset=True)

            if "nombre" in patch and patch["nombre"] != categoria.nombre:
                existente = uow.categorias.get_by_name(patch["nombre"])
                if existente and existente.id != categoria_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El nombre '{patch['nombre']}' ya está en uso por otra categoría"
                    )

            if "parent_id" in patch and patch["parent_id"] is not None:
                if patch["parent_id"] == categoria_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Una categoría no puede ser padre de sí misma"
                    )
                if patch["parent_id"] != categoria.parent_id:
                    self._get_or_404(uow, patch["parent_id"])
                    self._validar_jerarquia_padre(uow, categoria_id, patch["parent_id"])

            if "parent_id" in patch and patch["parent_id"] is None:
                # Si pasa a ser nodo raíz, sus hijos mantienen la referencia a esta categoría.
                patch["parent_id"] = None

            for field, value in patch.items():
                setattr(categoria, field, value)

            uow.categorias.update(categoria)
            return self._to_read_full(categoria)

    '''
    Si se borra un padre que tiene hijos, 
    los hijos quedan como principales o se borran? 
    Por ahora quedan como principales, no se borran.
    Revisar si es lo mejor.
    '''
    def delete(self, categoria_id: int) -> None:
        with self._uow as uow:
            categoria = self._get_or_404(uow, categoria_id)
            hijas = uow.categorias.get_by_parent(categoria_id)
            for hija in hijas:
                hija.parent_id = categoria.parent_id
                uow.categorias.update(hija)
            uow.categorias.delete(categoria)