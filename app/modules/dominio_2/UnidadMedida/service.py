from app.modules.dominio_2.UnidadMedida.models import UnidadMedida
from fastapi import HTTPException

from app.core.enums import EstadoFiltro
from app.modules.dominio_2.UnidadMedida.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaRead,
    UnidadMedidaUpdate,
)
from app.modules.dominio_2.UnidadMedida.unit_of_work import UnidadMedidaUnitOfWork

class UnidadMedidaService:
    def __init__(self, uow: UnidadMedidaUnitOfWork) -> None:
        self.uow = uow
    
    def get_or_404(self, unidad_medida_id: int, uow: UnidadMedidaUnitOfWork) -> UnidadMedida:
        unidad = uow.unidades_medida.get_by_id(unidad_medida_id)
        if not unidad:
            raise HTTPException(status_code=404, detail=f"Unidad de medida con ID {unidad_medida_id} no encontrada")
        return unidad

    def validar_nombre_unico(self, nombre: str, uow: UnidadMedidaUnitOfWork) -> None:
        nombre = uow.unidades_medida.get_by_name(nombre)
        if nombre:
            raise HTTPException(status_code=400, detail=f"El nombre '{nombre}' ya está en uso por otra unidad de medida")

    def validar_simbolo_unico(self, simbolo: str, uow: UnidadMedidaUnitOfWork) -> None:
        simbolo = uow.unidades_medida.get_by_simbolo(simbolo)
        if simbolo:
            raise HTTPException(status_code=400, detail=f"El simbolo '{simbolo}' ya está en uso por otra unidad de medida")

    def create(self, data: UnidadMedidaCreate) -> UnidadMedidaRead:
        with self.uow as uow:
            self.validar_nombre_unico(data.nombre, uow)
            self.validar_simbolo_unico(data.simbolo, uow)
            
            nueva_unidad = UnidadMedida.model_validate(data)
            uow.unidades_medida.add(nueva_unidad)

            return UnidadMedidaRead.model_validate(nueva_unidad)

    def get_all(self, offset: int = 0, limit: int = 20):
        with self.uow as uow:
            unidades = uow.unidades_medida.get_all_by_state(EstadoFiltro.ACTIVO, offset, limit)
            total = uow.unidades_medida.count_model(EstadoFiltro.ACTIVO)
            return {"data": [UnidadMedidaRead.model_validate(unidad) for unidad in unidades], "total": total}
    
    def get_by_id(self, unidad_id: int) -> UnidadMedidaRead:
        with self.uow as uow:
            unidad = self.get_or_404(unidad_id, uow)
            return UnidadMedidaRead.model_validate(unidad)

    def update(self, unidad_id: int, data: UnidadMedidaUpdate) -> UnidadMedidaRead:
        with self.uow as uow:
            unidad = self.get_or_404(unidad_id, uow)
            patch = data.model_dump(exclude_unset=True)

            if "nombre" in patch and patch["nombre"] != unidad.nombre:
                existente = uow.unidades_medida.get_by_name(patch["nombre"])
                if existente and existente.id != unidad_id:
                    raise HTTPException(status_code=400, detail=f"El nombre '{patch['nombre']}' ya está en uso por otra unidad de medida")
            
            if "simbolo" in patch and patch["simbolo"] != unidad.simbolo:
                existente = uow.unidades_medida.get_by_simbolo(patch["simbolo"])
                if existente and existente.id != unidad_id:
                    raise HTTPException(status_code=400, detail=f"El simbolo '{patch['simbolo']}' ya está en uso por otra unidad de medida")
            
            for field, value in patch.items():
                setattr(unidad, field, value)
            uow.unidades_medida.update(unidad)
            return UnidadMedidaRead.model_validate(unidad)

    def delete(self, unidad_id: int) -> None:
        with self.uow as uow:
            unidad = self.get_or_404(unidad_id, uow)
            uow.unidades_medida.delete(unidad)