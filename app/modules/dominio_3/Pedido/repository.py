from sqlmodel import Session, select, func

from app.core.repository import BaseRepository
from app.modules.dominio_3.Pedido.models import Pedido

class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session):
        super().__init__(session, Pedido)

    def get_all_by_usuario_id(self, usuario_id: int, offset: int = 0, limit: int = 20) -> list[Pedido]:
        statement = select(Pedido).where(Pedido.usuario_id == usuario_id).where(Pedido.deleted_at == None).order_by(Pedido.created_at.desc())
        return list(self.session.exec(statement.offset(offset).limit(limit)).all())
        
    def count_by_usuario_id(self, usuario_id: int) -> int:
        statement = select(func.count()).select_from(Pedido).where(Pedido.usuario_id == usuario_id).where(Pedido.deleted_at == None)
        return self.session.exec(statement).one()
    
    def get_all_active(self, offset: int = 0, limit: int = 20) -> list[Pedido]:
        statement = select(Pedido).where(Pedido.deleted_at == None).order_by(Pedido.created_at.desc())
        return list(self.session.exec(statement.offset(offset).limit(limit)).all())
        
    def count_all_active(self) -> int:
        statement = select(func.count()).select_from(Pedido).where(Pedido.deleted_at == None)
        return self.session.exec(statement).one()