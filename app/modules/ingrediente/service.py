from fastapi import HTTPException
from typing import cast

from app.modules.ingrediente.models import Ingrediente
from app.modules.ingrediente.schemas import (
    IngredienteCreate,
    ProductoBasicRead,
    IngredienteRead,
    IngredienteReadFull,
    IngredienteUpdate,
)
from app.modules.ingrediente.unit_of_work import IngredienteUnitOfWork


class IngredienteService:
    def __init__(self, uow: IngredienteUnitOfWork) -> None:
        self._uow = uow

    # ── Helpers privados ─────────────────────────────────────────────────────
    def _get_or_404(self, uow: IngredienteUnitOfWork, ingrediente_id: int) -> Ingrediente:
        ingrediente = uow.ingredientes.get_by_id(ingrediente_id)
        if not ingrediente:
            raise HTTPException(
                status_code=404,
                detail=f"Ingrediente con ID {ingrediente_id} no encontrado"
            )
        return ingrediente

    def _validar_nombre_unico(self, uow: IngredienteUnitOfWork, name: str) -> None:
        ingrediente = uow.ingredientes.get_by_name(name, include_deleted=True)
        if ingrediente:
            raise HTTPException(
                status_code=400,
                detail=f"El nombre '{name}' ya está en uso por otro ingrediente"
            )

    # ── Métodos públicos ───────────────────────────────────────────────────

    def _to_read_full(self, ingrediente: Ingrediente) -> IngredienteReadFull:
        productos = [
            ProductoBasicRead(id=cast(int, producto.id), nombre=producto.nombre)
            for producto in ingrediente.productos
            if not producto.borrado
        ]
        return IngredienteReadFull(
            id=cast(int, ingrediente.id),
            nombre=ingrediente.nombre,
            es_alergeno=ingrediente.es_alergeno,
            descripcion=ingrediente.descripcion,
            productos=productos,
        )

    def create(self, data: IngredienteCreate) -> IngredienteRead:
        with self._uow as uow:
            self._validar_nombre_unico(uow, data.nombre)
            nuevo_ingrediente = Ingrediente.model_validate(data)
            uow.ingredientes.create(nuevo_ingrediente)
            return IngredienteRead.model_validate(nuevo_ingrediente)

    def get_all(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            ingredientes = uow.ingredientes.get_all(offset, limit)
            total = uow.ingredientes.count()
            resultado = {"data": [self._to_read_full(i) for i in ingredientes], "total": total}
            return resultado

    def get_alergenos(self, offset: int = 0, limit: int = 20):
        with self._uow as uow:
            ingredientes = uow.ingredientes.get_alergenos(offset, limit)
            total = uow.ingredientes.count_alergenos()
            resultado = {"data": [self._to_read_full(i) for i in ingredientes], "total": total}
            return resultado
    
    def get_by_id(self, ingrediente_id: int) -> IngredienteReadFull:
        with self._uow as uow:
            ingrediente = self._get_or_404(uow, ingrediente_id)
            return self._to_read_full(ingrediente)
    
    def update(self, ingrediente_id: int, data: IngredienteUpdate) -> IngredienteRead:
        with self._uow as uow:
            ingrediente = self._get_or_404(uow, ingrediente_id)
            patch = data.model_dump(exclude_unset=True)

            if "nombre" in patch and patch["nombre"] != ingrediente.nombre:
                existente = uow.ingredientes.get_by_name(patch["nombre"])
                if existente and existente.id != ingrediente_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"El nombre '{patch['nombre']}' ya está en uso por otro ingrediente"
                    )

            for field, value in patch.items():
                setattr(ingrediente, field, value)

            uow.ingredientes.update(ingrediente)
            return IngredienteRead.model_validate(ingrediente)

    def delete(self, ingrediente_id: int) -> None:
        with self._uow as uow:
            ingrediente = self._get_or_404(uow, ingrediente_id)
            uow.ingredientes.delete(ingrediente)
