from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import SessionDep
from app.modules.dominio_1.usuario.schemas import UserCreate, UserPublic, Token
from app.modules.dominio_1.usuario.service import UsuarioService
from app.modules.dominio_1.usuario.unit_of_work import UsuarioUnitOfWork
from app.core.deps import get_current_active_user
from app.modules.dominio_1.usuario.models import Usuario

router = APIRouter(tags=["Auth & Usuarios"])

def get_usuario_service(session: SessionDep):
    uow = UsuarioUnitOfWork(session)
    return UsuarioService(uow)

UsuarioServiceDep = Annotated[UsuarioService, Depends(get_usuario_service)]

@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, service: UsuarioServiceDep):
    """Registra un nuevo usuario en la tienda."""
    return service.register(user_in)

@router.post("/auth/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UsuarioServiceDep
):
    """Recibe username y password plano. Devuelve el JWT."""
    return service.login(form_data)

@router.get("/usuarios/me", response_model=UserPublic)
def read_users_me(current_user: Annotated[Usuario, Depends(get_current_active_user)]):
    """
    Ruta protegida de prueba. 
    Si envías un JWT válido en el header, te devuelve tus datos.
    """
    return current_user