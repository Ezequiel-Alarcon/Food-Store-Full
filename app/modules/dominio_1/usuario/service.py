import hashlib
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional

from app.modules.dominio_1.usuario.unit_of_work import UsuarioUnitOfWork
from app.modules.dominio_1.usuario.schemas import UserCreate, UserUpdateAdmin, UserUpdateClient, Token
from app.modules.dominio_1.usuario.models import Rol,Usuario, RefreshToken
from app.core.security import hash_password, verify_password, create_access_token
from app.core.enums import EstadoFiltro

class UsuarioService:
    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def _get_user_of_404(self, usuario_id: int) -> Usuario:
        user = self.uow.usuarios.get_by_id(usuario_id)
        
        if not user or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return user

    def _crear_usuario_core(self, user_in: UserCreate, roles: List[Rol]) -> Usuario:
        """
        Método interno centralizado. 
        Maneja hashing, validación de email y persistencia.
        """
        # La verificación de email se hace aquí para que afecte a ambos flujos
        if self.uow.usuarios.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        nuevo_usuario = Usuario(
            nombre=user_in.nombre,
            apellido=user_in.apellido,
            email=user_in.email,
            celular=user_in.celular,
            password_hash=hash_password(user_in.password),
            roles=roles
        )
        
        return self.uow.usuarios.add(nuevo_usuario)
    
    def _update_user_core(self, usuario_id: int, data_dict: dict, nuevos_roles: Optional[List[Rol]] = None) -> Usuario:
        user = self._get_user_of_404(usuario_id)

        for key, value in data_dict.items():
            setattr(user, key, value)

        if nuevos_roles is not None:
            user.roles = nuevos_roles

        return user


    # ==========================================
    # --- FLUJOS PÚBLICOS Y ADMINISTRATIVOS ---
    # ==========================================

    def register(self, user_in: UserCreate) -> Usuario:
        """Flujo para clientes: setea rol 'CLIENT' automáticamente."""
        with self.uow:
            rol_default = self.uow.roles.get_by_codigo("CLIENT")
            if not rol_default:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Configuración de sistema inválida: Rol 'CLIENT' no existe."
                )
            return self._crear_usuario_core(user_in, [rol_default])


    def create_user_admin(self, user_in: UserCreate, roles_codigos: List[str]) -> Usuario:
        """Flujo para Admin: permite especificar una lista de códigos de roles."""
        with self.uow:
            objetos_roles = []
            for codigo in roles_codigos:
                rol = self.uow.roles.get_by_codigo(codigo)
                if not rol:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El código de rol '{codigo}' no es válido."
                    )
                objetos_roles.append(rol)
            
            return self._crear_usuario_core(user_in, objetos_roles)
        


    def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        email_ingresado = form_data.username 
        password_ingresada = form_data.password

        with self.uow as uow:
            user = uow.usuarios.get_by_email(email_ingresado)
            
            # Validamos existencia, clave y que no esté baneado
            if not user or not verify_password(password_ingresada, user.password_hash) or user.deleted_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # --- GENERACIÓN DE TOKENS ---
            
            # 1. Access Token
            roles_codigos = [rol.codigo for rol in user.roles]
            access_token = create_access_token(
                data={"sub": str(user.id), "roles": roles_codigos}
            )

            # 2. Refresh Token
            token_hash = hashlib.sha256(access_token.encode()).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

            nuevo_rt = RefreshToken(
                usuario_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            
            uow._session.add(nuevo_rt) 

            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        

    def update_profile(self, usuario_id: int, user_in: UserUpdateClient) -> Usuario:
        with self.uow:
            data = user_in.model_dump(exclude_unset=True)
            return self._update_user_core(usuario_id, data_dict=data)
    

    def update_user_by_admin(self, user_id: int, user_in: UserUpdateAdmin) -> Usuario:
        with self.uow as uow:
            data = user_in.model_dump(exclude_unset=True)

            roles_codigos = data.pop("roles_codigos", None)

            objetos_roles = None
            if roles_codigos is not None:
                objetos_roles = []
                for codigo in roles_codigos:
                    rol = uow.roles.get_by_id(codigo)
                    if not rol:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El codigo de rol {codigo} no es valido"
                        )
                    objetos_roles.append(rol)

            return self._update_user_core(user_id, data_dict=data, nuevos_roles=objetos_roles)


    # ==========================================
    # --- FLUJO DE ADMIN (Privado) ---
    # ==========================================

    def get_all_users(self,offset: int = 0, limit: int = 20, rol_codigo: Optional[str] = None):
        with self.uow:
            usuarios_paginados = self.uow.usuarios.get_paged_users(offset=offset, limit=limit, rol_codigo=rol_codigo, state = EstadoFiltro.ACTIVO)

            total = self.uow.usuarios.count_model(state=EstadoFiltro.ACTIVO)
        return{
            "data": usuarios_paginados,
            "total": total
        }

    def desactivar_usuario(self, user_id: int):
        """Aplica el borrado lógico."""
        with self.uow as uow:
            user = self._get_user_of_404(user_id)
            uow.usuarios.delete(user)
            return {"mensaje": f"Usuario {user.email} eliminado correctamente"}