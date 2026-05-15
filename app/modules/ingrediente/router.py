from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.modules.ingrediente.schemas import (
    IngredienteCreate,
    IngredienteList,
    IngredienteRead,
    IngredienteReadFull,
    IngredienteUpdate
)
from app.modules.ingrediente.unit_of_work import IngredienteUnitOfWork
from app.modules.ingrediente.service import IngredienteService

router = APIRouter()

# ── Factory: inyecta el Service con la Session ──────────────────────────
def get_ingrediente_service(session: Session = Depends(get_session)) -> IngredienteService:
    return IngredienteService(IngredienteUnitOfWork(session))

# ── Endpoints ───────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=IngredienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ingrediente"
)
def create_ingrediente(
    data: IngredienteCreate,
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.create(data)

@router.get(
    "/",
    response_model=IngredienteList,
    summary="Listar todos los ingredientes (paginado)"
)
def list_ingredientes(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.get_all(offset=offset, limit=limit)

@router.get(
    "/alergenos",
    response_model=IngredienteList,
    summary="Listar todos los ingredientes alérgenos"
)
def list_ingredientes_alergenos(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.get_alergenos(offset=offset, limit=limit)

@router.get(
    "/{ingrediente_id}",
    response_model=IngredienteReadFull,
    summary="Obtener ingrediente por ID"
)
def get_ingrediente(
    ingrediente_id: Annotated[int, Path(ge=1, description="ID del ingrediente")],
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.get_by_id(ingrediente_id)

@router.patch(
    "/{ingrediente_id}",
    response_model=IngredienteRead,
    summary="Actualizar un ingrediente (parcial)"
)
def update_ingrediente(
    ingrediente_id: Annotated[int, Path(ge=1, description="ID del ingrediente")],
    data: IngredienteUpdate,
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.update(ingrediente_id, data)

@router.delete(
    "/{ingrediente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un ingrediente"
)
def delete_ingrediente(
    ingrediente_id: Annotated[int, Path(ge=1, description="ID del ingrediente")],
    svc: IngredienteService = Depends(get_ingrediente_service)
):
    return svc.delete(ingrediente_id)
