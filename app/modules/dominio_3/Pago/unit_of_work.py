from app.core.unit_of_work import UnitOfWork
from app.modules.dominio_3.Pago.repository import PagoRepository

class PagoUnitOfWork(UnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.pagos = PagoRepository(self._session)
        return self
