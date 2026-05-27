from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session

from app.core.deps import require_role
from app.core.database import get_session
from app.core.enums import EstadoFiltro
from app.modules.dominio_2.UnidadMedida.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaList,
    UnidadMedidaRead,
    UnidadMedidaUpdate
)
from app.modules.dominio_2.UnidadMedida.service import UnidadMedidaService

router = APIRouter()

def get_unidad_medida_service(session: Session = Depends(get_session)) -> UnidadMedidaService:
    return UnidadMedidaService(session)

# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED, summary="Crear unidad de medida", dependencies=[Depends(require_role(["ADMIN"]))])
def create_unidad_medida(data: UnidadMedidaCreate, svc: UnidadMedidaService = Depends(get_unidad_medida_service)):
    return svc.create(data)

@router.get("/", response_model=UnidadMedidaList, summary="Listar unidades de medida")
def list_unidades_medida(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    estado: Annotated[EstadoFiltro, Query(description="Filtrar por estado")] = EstadoFiltro.ACTIVO,
    svc: UnidadMedidaService = Depends(get_unidad_medida_service)
):
    return svc.get_all_unidades(offset=offset, limit=limit, estado=estado)

@router.get("/{unidad_id}", response_model=UnidadMedidaRead, summary="Obtener unidad de medida")
def get_unidad_medida(
    unidad_id: Annotated[int, Path(ge=1)],
    incluir_eliminado: Annotated[bool, Query(description="Permitir ver el registro aunque esté eliminado")] = False,
    svc: UnidadMedidaService = Depends(get_unidad_medida_service)
):
    return svc.get_by_id(unidad_id, allow_deleted=incluir_eliminado)

@router.patch("/{unidad_id}", response_model=UnidadMedidaRead, summary="Actualizar unidad de medida", dependencies=[Depends(require_role(["ADMIN"]))])
def update_unidad_medida(
    unidad_id: Annotated[int, Path(ge=1)], 
    data: UnidadMedidaUpdate, 
    svc: UnidadMedidaService = Depends(get_unidad_medida_service)
):
    return svc.update(unidad_id, data)

@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar unidad de medida", dependencies=[Depends(require_role(["ADMIN"]))])
def delete_unidad_medida(
    unidad_id: Annotated[int, Path(ge=1)], 
    svc: UnidadMedidaService = Depends(get_unidad_medida_service)
):
    return svc.delete(unidad_id)