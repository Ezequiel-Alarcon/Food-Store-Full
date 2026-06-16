"""
Endpoint transversal para subir imágenes a Cloudinary.

Devuelve la `imagen_url` y el `imagen_public_id` que el cliente deberá
enviar luego en el cuerpo JSON de los endpoints de creación/actualización
de los módulos que soportan imagen (Categoría, Ingrediente, Producto).

Convención del proyecto: los CRUDs siguen aceptando JSON, por lo que
el upload es un paso previo separado (multipart/form-data). Esto evita
romper contratos existentes y mantiene el patrón JSON del proyecto.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlmodel import Field, SQLModel

from app.core.cloudinary_service import ImagenSubida, subir_imagen
from app.core.deps import require_role


TipoEntidadImagen = Literal["categoria", "ingrediente", "producto"]


class ImagenUploadResponse(SQLModel):
    """Respuesta normalizada que el cliente persiste junto a la entidad."""
    imagen_url: str = Field(..., description="URL pública (https) de la imagen")
    imagen_public_id: str = Field(
        ...,
        description="ID interno en Cloudinary, requerido para reemplazo/borrado",
    )


router = APIRouter(prefix="/imagenes", tags=["Imágenes"])


@router.post(
    "/upload",
    response_model=ImagenUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen a Cloudinary",
    description=(
        "Sube un archivo de imagen (jpg/png/webp/gif/avif, máx 5 MB) a "
        "la carpeta correspondiente al `tipo` de entidad y devuelve la "
        "URL pública junto con el public_id para almacenarlo en la "
        "entidad. Reservado a ADMIN."
    ),
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def upload_imagen(
    archivo: Annotated[UploadFile, File(description="Archivo de imagen")],
    tipo: Annotated[
        TipoEntidadImagen,
        Form(description="Carpeta destino en Cloudinary según la entidad"),
    ] = "categoria",
) -> ImagenUploadResponse:
    resultado: ImagenSubida = subir_imagen(archivo, tipo=tipo)
    return ImagenUploadResponse(
        imagen_url=resultado.imagen_url,
        imagen_public_id=resultado.imagen_public_id,
    )
