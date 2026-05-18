"""
Dependencias de autenticación y autorización para inyectar vía Depends().

Flujo de resolución:
    Request
      → oauth2_scheme extrae el Bearer token del header Authorization
      → get_current_user abre un UoW, decodifica el JWT, carga el usuario
      → get_current_active_user verifica que disabled=False
      → require_role([...]) verifica que el rol del usuario esté permitido

Separación semántica de errores HTTP:
    401 = no autenticado (sin token / token inválido / expirado)
    403 = autenticado pero sin permisos (rol insuficiente)

Capa: Core (dependencias transversales)
Conoce a: UoW, Security, Model
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token

from app.modules.dominio_1.usuario.unit_of_work import UsuarioUnitOfWork
from app.core.database import SessionDep
from app.modules.dominio_1.usuario.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Creamos una pequeña dependencia para instanciar tu UoW
def get_usuario_uow(session: SessionDep) -> UsuarioUnitOfWork:
    return UsuarioUnitOfWork(session)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    # Inyectamos tu UoW modular acá
    uow: Annotated[UsuarioUnitOfWork, Depends(get_usuario_uow)], 
) -> Usuario:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Como usamos un UoW específico, "uow.usuarios" existe y autocompleta perfecto
    with uow:
        user = uow.usuarios.get_by_username(username)

    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """Verifica que el usuario autenticado no esté desactivado."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuenta de usuario desactivada",
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Control de acceso basado en múltiples roles.
    Comprueba si el usuario tiene al menos uno de los roles requeridos.
    """
    async def role_checker(
        current_user: Annotated[Usuario, Depends(get_current_active_user)],
    ) -> Usuario:
        # Extraemos los nombres de los roles que tiene el usuario
        user_roles_names = [rol.nombre for rol in current_user.roles]
        
        # Verificamos si hay alguna intersección entre los roles del user y los permitidos
        has_permission = any(rol in allowed_roles for rol in user_roles_names)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permisos insuficientes. Tus roles son '{user_roles_names}'. "
                    f"Se requiere al menos uno de: {allowed_roles}"
                ),
            )
        return current_user

    return role_checker