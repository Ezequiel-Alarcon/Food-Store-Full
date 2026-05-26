from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token
from app.core.deps import get_current_active_user, get_uow, require_role
from app.modules.dominio_1.usuario.schemas import UserCreate, UserPublic, UserUpdateClient, UserUpdateAdmin,UserPaginationResponse, UserPublicAdminPanel, UserCreateAdmin
from app.modules.dominio_1.usuario.service import UsuarioService
from app.modules.dominio_1.usuario.unit_of_work import UsuarioUnitOfWork

# ==========================================
# DEPENDENCIAS DEL MÓDULO
# ==========================================
def get_usuario_service(uow: Annotated[UsuarioUnitOfWork, Depends(get_uow)]) -> UsuarioService:
    return UsuarioService(uow)

UsuarioServiceDep = Annotated[UsuarioService, Depends(get_usuario_service)]
CurrentUser = Annotated[UserPublic, Depends(get_current_active_user)]

# ==========================================
# GRUPO 1: AUTENTICACIÓN (Público)
# ==========================================
auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])

@auth_router.post("/login")
def login(
    response: Response, 
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    svc: UsuarioServiceDep
) -> Any:
    
    token_obj = svc.login(form_data)
    
    response.set_cookie(
        key="access_token",
        value=token_obj.access_token,
        httponly=True,
        max_age=token_obj.expires_in,
        expires=token_obj.expires_in,
        samesite="lax",
        secure=False, # Poner en True si usás HTTPS en producción
    )
    return {"mensaje": "Login exitoso", "access_token": token_obj.access_token, "token_type": "bearer"}

@auth_router.post("/logout")
def logout(response: Response) -> Any:
    response.delete_cookie(key="access_token")
    return {"mensaje": "Logout exitoso"}

@auth_router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, svc: UsuarioServiceDep) -> Any:
    """Registra un cliente nuevo y le asigna el rol CLIENT automáticamente."""
    return svc.register(data)

# ==========================================
# GRUPO 2: PERFIL DEL CLIENTE (Privado)
# ==========================================
usuarios_router = APIRouter(prefix="/usuarios", tags=["Usuarios (Mi Perfil)"])

@usuarios_router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """Devuelve los datos del usuario logueado actualmente."""
    return current_user

@usuarios_router.patch("/me", response_model=UserPublic)
def update_user_me(data: UserUpdateClient, current_user: CurrentUser, svc: UsuarioServiceDep) -> Any:
    """Actualiza los datos básicos del usuario logueado (sin tocar roles)."""
    return svc.update_profile(current_user.id, data)


# ==========================================
# GRUPO 3: PANEL ADMINISTRATIVO
# ==========================================
admin_router = APIRouter(
    prefix="/admin/usuarios", 
    tags=["Panel de Administración - Usuarios"],
    dependencies=[Depends(require_role(["ADMIN"]))]
)

@admin_router.post("/createUser", response_model=UserPublicAdminPanel, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    data: UserCreateAdmin, 
    current_user: CurrentUser, 
    svc: UsuarioServiceDep
) -> Any:
    """El Admin crea un usuario asignándole roles específicos manualmente."""
    
    # 1. Separamos los datos base del usuario de la lista de roles
    datos_usuario = data.model_dump(exclude={"roles_codigos"})
    user_in = UserCreate(**datos_usuario)
    
    return svc.create_user_admin(user_in=user_in, roles_codigos=data.roles_codigos)

@admin_router.get("/", response_model=UserPaginationResponse)
def get_all_users(
    current_user: CurrentUser,
    svc: UsuarioServiceDep, 
    offset: int = 0, 
    limit: int = 20, 
    rol_codigo: str | None = None
) -> Any:
    """Lista todos los usuarios activos. Permite paginación y filtrado por rol."""
    return svc.get_all_users(offset=offset, limit=limit, rol_codigo=rol_codigo)

@admin_router.patch("/{user_id}", response_model=UserPublicAdminPanel)
def update_user_by_admin(user_id: int, data: UserUpdateAdmin, current_user: CurrentUser, svc: UsuarioServiceDep) -> Any:
    """El Admin actualiza los datos y/o los roles de cualquier usuario."""
    return svc.update_user_by_admin(user_id, data)

@admin_router.delete("/{user_id}")
def delete_user(user_id: int, current_user: CurrentUser,svc: UsuarioServiceDep) -> Any:
    """Aplica un borrado lógico (soft delete) a un usuario."""
    return svc.desactivar_usuario(user_id)