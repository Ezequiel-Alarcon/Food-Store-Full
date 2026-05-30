from typing import Annotated

from fastapi import APIRouter, Depends, Response, status, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import get_current_active_user, require_role
from app.modules.dominio_1.usuario.schemas import UserPublic
from app.modules.dominio_3.Pedido.schemas import PedidoCambioEstado, PedidoCreate, PedidoReadFull, PedidoList
from app.modules.dominio_3.HistorialEstadoPedido.schemas import HistorialEstadoPedidoRead
from app.modules.dominio_3.Pedido.service import PedidoService
from app.modules.dominio_3.Pedido.unit_of_work import PedidoUnitOfWork

router = APIRouter()

CurrentUser = Annotated[UserPublic, Depends(get_current_active_user)]

def get_pedido_service(session: Session = Depends(get_session)) -> PedidoService:
    return PedidoService(PedidoUnitOfWork(session))


# ══════════════════════════════════════════════════════
# CLIENT — operaciones sobre sus propios pedidos
# ══════════════════════════════════════════════════════

@router.post("/", response_model=PedidoReadFull, status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_role(["CLIENT"]))])
def crear_pedido(
    data: PedidoCreate,
    current_user: CurrentUser,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.crear_pedido(data, current_user.id)


@router.get("/mis-pedidos", response_model=PedidoList,dependencies=[Depends(require_role(["CLIENT"]))])
def obtener_mis_pedidos(
    current_user: CurrentUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoList:
    return service.obtener_pedidos_por_usuario(current_user.id, offset, limit)


@router.get("/mis-pedidos/{pedido_id}", response_model=PedidoReadFull,dependencies=[Depends(require_role(["CLIENT"]))])
def obtener_mi_pedido(
    pedido_id: int,
    current_user: CurrentUser,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.obtener_pedido_propio(pedido_id, current_user.id)


@router.patch("/mis-pedidos/{pedido_id}/cancelar", response_model=PedidoReadFull,dependencies=[Depends(require_role(["CLIENT"]))])
def cancelar_mi_pedido(
    pedido_id: int,
    data: PedidoCambioEstado,
    current_user: CurrentUser,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.cancelar_pedido_propio(pedido_id, current_user.id, data)


# ══════════════════════════════════════════════════════
# ADMIN / PEDIDOS — visibilidad y gestión total
# ══════════════════════════════════════════════════════

@router.get("/", response_model=PedidoList,dependencies=[Depends(require_role(["ADMIN", "PEDIDOS"]))])
def obtener_todos_los_pedidos(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoList:
    return service.obtener_todos_los_pedidos(offset, limit)


@router.get("/{pedido_id}", response_model=PedidoReadFull,dependencies=[Depends(require_role(["ADMIN", "PEDIDOS"]))])
def obtener_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.obtener_pedido_por_id(pedido_id)


@router.get("/{pedido_id}/historial", response_model=list[HistorialEstadoPedidoRead],dependencies=[Depends(require_role(["ADMIN", "PEDIDOS"]))])
def obtener_historial_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> list[HistorialEstadoPedidoRead]:
    return service.obtener_historial_pedido(pedido_id)


@router.patch("/{pedido_id}/estado", response_model=PedidoReadFull,dependencies=[Depends(require_role(["ADMIN", "PEDIDOS"]))])
def cambiar_estado_pedido(
    pedido_id: int,
    data: PedidoCambioEstado,
    current_user: CurrentUser,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.cambiar_estado_pedido(pedido_id, data, current_user.id)


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_role(["ADMIN"]))])
def eliminar_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> Response:
    service.eliminar_pedido(pedido_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)