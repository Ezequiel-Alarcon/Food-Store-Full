from fastapi import Response
from app.modules.dominio_3.Pedido.schemas import PedidoCambioEstado
from app.modules.dominio_3.HistorialEstadoPedido.schemas import HistorialEstadoPedidoRead
from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.core.database import get_session
from app.modules.dominio_3.Pedido.schemas import PedidoCreate, PedidoReadFull
from app.modules.dominio_3.Pedido.service import PedidoService
from app.modules.dominio_3.Pedido.unit_of_work import PedidoUnitOfWork


router = APIRouter()


def get_pedido_service(session: Session = Depends(get_session)) -> PedidoService:
    return PedidoService(PedidoUnitOfWork(session))



@router.post("/", response_model=PedidoReadFull, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: PedidoCreate,
    usuario_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.crear_pedido(data, usuario_id)

@router.get("/", response_model=list[PedidoReadFull])
def obtener_pedidos_por_usuario(
    usuario_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> list[PedidoReadFull]:
    return service.obtener_pedidos_por_usuario(usuario_id)

@router.get("/{pedido_id}", response_model=PedidoReadFull)
def obtener_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.obtener_pedido_por_id(pedido_id)

@router.get("/{pedido_id}/historial", response_model=list[HistorialEstadoPedidoRead])
def obtener_historial_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> list[HistorialEstadoPedidoRead]:
    return service.obtener_historial_pedido(pedido_id)

@router.patch("/{pedido_id}/estado", response_model=PedidoReadFull)
def cambiar_estado_pedido(
    pedido_id: int,
    data: PedidoCambioEstado,
    usuario_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> PedidoReadFull:
    return service.cambiar_estado_pedido(pedido_id, data, usuario_id)

@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pedido(
    pedido_id: int,
    service: PedidoService = Depends(get_pedido_service),
) -> Response:
    service.eliminar_pedido(pedido_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)