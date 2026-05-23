from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.modules.dominio_3.DetallePedido.models import DetallePedido

class DetallePedidoRepository(BaseRepository[DetallePedido]):
    def __init__(self, session: Session):
        super().__init__(session, DetallePedido)

    def get_all_by_pedido_id(self, pedido_id: int) -> list[DetallePedido]:
        statement = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id).order_by(DetallePedido.created_at.asc())
        return list(self.session.exec(statement).all())