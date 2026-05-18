from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.dominio_1.usuario.repository import UsuarioRepository, RolRepository

class UsuarioUnitOfWork(UnitOfWork):
    def __init__(self, session: Session):
        super().__init__(session)
        self.usuarios = UsuarioRepository(session)
        self.roles = RolRepository(session)