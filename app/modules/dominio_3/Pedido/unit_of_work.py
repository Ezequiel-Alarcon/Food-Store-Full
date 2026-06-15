from sqlmodel import Session
from fastapi import Depends
from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.dominio_2.producto.repository import ProductoRepository
from app.modules.dominio_2.ingrediente.repository import IngredienteRepository
from app.modules.dominio_1.usuario.repository import UsuarioRepository
from app.modules.dominio_3.DetallePedido.repository import DetallePedidoRepository
from app.modules.dominio_3.EstadoPedido.repository import EstadoPedidoRepository
from app.modules.dominio_3.FormaPago.repository import FormaPagoRepository
from app.modules.dominio_3.HistorialEstadoPedido.repository import HistorialEstadoPedidoRepository
from app.modules.dominio_3.Pedido.repository import PedidoRepository

class PedidoUnitOfWork(UnitOfWork):
    def __init__(self, session: Session = Depends(get_session)):
        # Inicializa la session en el UnitOfWork base
        super().__init__(session)
        # Repositories que participan en crear/consultar pedidos
        self.pedidos = PedidoRepository(session)
        self.detalles = DetallePedidoRepository(session)
        self.historial = HistorialEstadoPedidoRepository(session)
        self.estados = EstadoPedidoRepository(session)
        self.formas_pago = FormaPagoRepository(session)
        self.productos = ProductoRepository(session)
        self.ingredientes = IngredienteRepository(session)
        self.usuarios = UsuarioRepository(session)