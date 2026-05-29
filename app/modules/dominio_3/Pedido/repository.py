from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.modules.dominio_3.Pedido.models import Pedido

class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session):
        super().__init__(session, Pedido)

    def get_all_by_usuario_id(self, usuario_id: int) -> list[Pedido]:
        statement = select(Pedido).where(Pedido.usuario_id == usuario_id).where(Pedido.deleted_at == None).order_by(Pedido.created_at.desc())
        return list(self.session.exec(statement).all())
    
    def get_all_active(self) -> list[Pedido]:
        statement = select(Pedido).where(Pedido.deleted_at == None).order_by(Pedido.created_at.desc())
        return list(self.session.exec(statement).all())