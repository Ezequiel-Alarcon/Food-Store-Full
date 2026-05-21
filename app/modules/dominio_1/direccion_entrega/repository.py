from typing import Optional, Sequence
import uuid
from sqlmodel import select, Session
from app.core.repository import BaseRepository
from app.core.enums import EstadoFiltro
from app.modules.dominio_1.direccion_entrega.models import DireccionEntrega # Asegurá el path de tu modelo

class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session):
        super().__init__(session, DireccionEntrega)

    def get_by_usuario(self, usuario_id: uuid.UUID, state: EstadoFiltro = EstadoFiltro.ACTIVO) -> Sequence[DireccionEntrega]:
        """Trae todas las direcciones de un usuario específico respetando el borrado lógico."""
        statement = select(DireccionEntrega).where(DireccionEntrega.usuario_id == usuario_id)
        
        # Reutilizamos tu filtro de estado genérico del padre
        statement = self._filter_state(statement, state)
        
        return self.session.exec(statement).all()

    def get_principal_by_usuario(self, usuario_id: uuid.UUID) -> Optional[DireccionEntrega]:
        """Busca la dirección que actualmente está seteada como principal para el usuario."""
        statement = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.es_principal,
            DireccionEntrega.deleted_at.is_(None) # Solo buscamos entre las activas
        )
        return self.session.exec(statement).first()