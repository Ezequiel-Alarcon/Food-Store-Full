import uuid
from typing import List
from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.service import base_service
from app.core.enums import EstadoFiltro
from app.modules.dominio_1.usuario.unit_of_work import UsuarioUnitOfWork
from app.modules.dominio_1.direccion_entrega.models import DireccionEntrega
from app.modules.dominio_1.direccion_entrega.schemas import DireccionCreate, DireccionUpdate
from app.modules.dominio_1.direccion_entrega.repository import DireccionRepository

class DireccionService(base_service[DireccionEntrega, DireccionCreate, DireccionUpdate, UsuarioUnitOfWork]):
    def __init__(self, session: Session):
        uow = UsuarioUnitOfWork(session)
        super().__init__(
            session=session,
            uow_instance=uow,
            repo_name="direcciones",
            model_class=DireccionEntrega
        )

    @property
    def repo(self) -> DireccionRepository: # ¡Acá le damos el tipo exacto!
        return self.uow.direcciones

    def _get_direccion_segura_or_404(self, direccion_id: int, usuario_id: uuid.UUID) -> DireccionEntrega:
        """Busca la dirección y valida de forma estricta la propiedad del recurso."""
        direccion = self._get_or_404(direccion_id)
        if direccion.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para operar sobre esta dirección"
            )
        return direccion

    # ================= OVERRIDES CON LÓGICA DE NEGOCIO =================

    def crear_direccion_propia(self, usuario_id: uuid.UUID, item_in: DireccionCreate) -> DireccionEntrega:
        """Crea una dirección asegurando las reglas de negocio de 'es_principal'."""
        with self.uow:
            # Lógica específica: verificar si es la primera para hacerla favorita
            mis_direcciones = self.repo.get_by_usuario(usuario_id)
            es_primera = len(mis_direcciones) == 0

            # Reutilizamos el molde del modelo del padre
            nueva_direccion = self.model_class(
                **item_in.model_dump(),
                usuario_id=usuario_id,
                es_principal=es_primera
            )
            
            self.repo.add(nueva_direccion)
            return nueva_direccion

    def listar_mis_direcciones(self, usuario_id: uuid.UUID) -> List[DireccionEntrega]:
        """Usa el repositorio específico inyectado en el UoW."""
        with self.uow:
            return self.repo.get_by_usuario(usuario_id, state=EstadoFiltro.ACTIVO)

    def actualizar_direccion_propia(self, direccion_id: int, usuario_id: uuid.UUID, item_in: DireccionUpdate) -> DireccionEntrega:
        """Actualiza de forma segura consumiendo el formateador del padre."""
        with self.uow:
            # 1. Validamos propiedad del recurso
            direccion_db = self._get_direccion_segura_or_404(direccion_id, usuario_id)
            
            # 2. Reutilizamos la lógica del bucle dinámico del padre sin abrir otra transacción
            self._apply_update_fields(direccion_db, item_in)
            
            # 3. Guardamos a través del repositorio genérico
            self.repo.update(direccion_db)
            return direccion_db

    def eliminar_direccion_propia(self, direccion_id: int, usuario_id: uuid.UUID):
        with self.uow:
            direccion_db = self._get_direccion_segura_or_404(direccion_id, usuario_id)
            self.repo.delete(direccion_db)
            return {"message": "Dirección eliminada correctamente"}

    def marcar_como_principal(self, direccion_id: int, usuario_id: uuid.UUID) -> DireccionEntrega:
        """Regla transaccional compleja: baja la principal vieja y sube la nueva."""
        with self.uow:
            nueva_principal = self._get_direccion_segura_or_404(direccion_id, usuario_id)

            if nueva_principal.es_principal:
                return nueva_principal

            # Buscamos si el usuario ya tenía una favorita activa
            vieja_principal = self.repo.get_principal_by_usuario(usuario_id)
            if vieja_principal:
                vieja_principal.es_principal = False
                self.repo.update(vieja_principal)

            nueva_principal.es_principal = True
            self.repo.update(nueva_principal)
            return nueva_principal