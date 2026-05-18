from typing import Optional
from sqlmodel import select, Session
from app.modules.dominio_1.usuario.models import Usuario, Rol
from app.core.repository import BaseRepository

class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        # Le pasamos la sesión y el modelo al BaseRepository
        super().__init__(session, Usuario)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Búsqueda específica de este dominio."""
        statement = select(Usuario).where(Usuario.email == email).where(Usuario.deleted_at.is_(None))
        return self.session.exec(statement).first()


class RolRepository(BaseRepository[Rol]):
    def __init__(self, session: Session):
        super().__init__(session, Rol)

    def get_by_codigo(self, codigo: str) -> Optional[Rol]:

        return self.session.get(Rol, codigo)