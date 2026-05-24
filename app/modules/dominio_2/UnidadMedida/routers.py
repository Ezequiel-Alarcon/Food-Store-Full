from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.modules.dominio_2.UnidadMedida.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaList,
    UnidadMedidaRead,
    UnidadMedidaUpdate,
)
from app.modules.dominio_2.UnidadMedida.service import UnidadMedidaService
from app.modules.dominio_2.UnidadMedida.unit_of_work import UnidadMedidaUnitOfWork


router = APIRouter()

def get_unidad_medida_service(
    session: Session = Depends(get_session)
) -> UnidadMedidaService:
    return UnidadMedidaService(UnidadMedidaUnitOfWork(session))

@router.post("/", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED, summary="Crear unidad de medida")
def create_unidad_medida(data: UnidadMedidaCreate, svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.create(data)

@router.get("/", response_model=UnidadMedidaList, summary="Listar unidades de medida")
def list_unidades_medida(offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20, svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.get_all(offset=offset, limit=limit)

@router.get("/{unidad_id}", response_model=UnidadMedidaRead, summary="Obtener unidad de medida por ID")
def get_unidad_medida(unidad_id: Annotated[int, Path(ge=1)], svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.get_by_id(unidad_id)
    
@router.patch("/{unidad_id}", response_model=UnidadMedidaRead, summary="Actualizar unidad de medida")
def update_unidad_medida(unidad_id: Annotated[int, Path(ge=1)], data: UnidadMedidaUpdate, svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.update(unidad_id, data)
    
@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar unidad de medida")
def delete_unidad_medida(unidad_id: Annotated[int, Path(ge=1)], svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.delete(unidad_id)