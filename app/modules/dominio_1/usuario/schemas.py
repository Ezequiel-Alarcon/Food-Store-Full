from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
import uuid

# --- Sub-Schemas para mostrar en la respuesta pública ---
class RolPublic(BaseModel):
    codigo: str
    nombre: str
    # descripcion: Optional[str] = None

# --- Entrada de datos (POST /register) ---
class UserCreate(BaseModel):
    nombre: str = Field(..., max_length=80)
    apellido: str = Field(..., max_length=80)
    email: EmailStr
    celular: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8)
 
class UserUpdateClient(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=80)
    apellido: Optional[str] = Field(default=None, max_length=80)
    celular: Optional[str] = Field(default=None, max_length=20)

class UserUpdateAdmin(UserUpdateClient):
    roles_codigos: Optional[List[str]] = None

    
# --- Salida de datos (GET /me, Respuesta de Login/Register) ---
class UserPublic(BaseModel):
    id: uuid.UUID
    nombre: str
    apellido: str
    email: str
    celular: Optional[str] = None

class UserPublicAdminPanel(UserPublic):
    rol: RolPublic
    

# --- Respuesta del Login ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int