from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

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
    password: str = Field(min_length=8)# poner limite
    
# --- Salida de datos (GET /me, Respuesta de Login/Register) ---
class UserPublic(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    celular: Optional[str] = None
    roles: List[RolPublic] = [] 
    

# --- Respuesta del Login ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int