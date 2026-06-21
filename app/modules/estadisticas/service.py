from datetime import date
from typing import List
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.estadisticas.schemas import (
    VentasPeriodoItem,
    ProductoTopItem,
    PedidosEstadoItem,
    IngresosResponse,
    ResumenResponse
)

class EstadisticasService:
    def __init__(self, uow: PedidoUnitOfWork):
        self.uow = uow

    def get_ventas_periodo(self, desde: date, hasta: date, agrupacion: str = 'day') -> List[VentasPeriodoItem]:
        with self.uow:
            rows = self.uow.pedidos.get_ventas_periodo(desde, hasta, agrupacion)
            return [
                VentasPeriodoItem(
                    fecha=row.fecha,
                    total_ventas=row.total_ventas or 0,
                    cantidad_pedidos=row.cantidad_pedidos
                ) for row in rows
            ]

    def get_productos_top(self, desde: date, hasta: date, limit: int = 5) -> List[ProductoTopItem]:
        with self.uow:
            rows = self.uow.detalles.get_productos_top(desde, hasta, limit)
            return [
                ProductoTopItem(
                    nombre=row.nombre,
                    ingresos=row.ingresos or 0,
                    cantidad_vendida=row.cantidad_vendida or 0
                ) for row in rows
            ]

    def get_pedidos_por_estado(self) -> List[PedidosEstadoItem]:
        with self.uow:
            rows = self.uow.pedidos.get_pedidos_por_estado()
            return [
                PedidosEstadoItem(
                    estado_codigo=row.estado_codigo,
                    cantidad=row.cantidad
                ) for row in rows
            ]

    def get_ingresos_por_forma_pago(self, desde: date, hasta: date) -> List[IngresosResponse]:
        with self.uow:
            rows = self.uow.pedidos.get_ingresos_por_forma_pago(desde, hasta)
            return [
                IngresosResponse(
                    forma_pago_codigo=row.forma_pago_codigo,
                    total=row.total or 0,
                    cantidad=row.cantidad
                ) for row in rows
            ]

    def get_resumen_kpis(self) -> ResumenResponse:
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        
        with self.uow:
            # Ventas de hoy
            hoy_data = self.uow.pedidos.get_ventas_periodo(hoy, hoy, 'day')
            ventas_hoy = hoy_data[0].total_ventas if hoy_data and hoy_data[0].total_ventas else 0
            
            # Ingresos del mes y ticket promedio
            mes_data = self.uow.pedidos.get_ventas_periodo(inicio_mes, hoy, 'month')
            ingresos_mes = mes_data[0].total_ventas if mes_data and mes_data[0].total_ventas else 0
            cant_mes = mes_data[0].cantidad_pedidos if mes_data and mes_data[0].cantidad_pedidos else 0
            ticket_promedio = (ingresos_mes / cant_mes) if cant_mes > 0 else 0
            
            # Pedidos activos (Todos menos ENTREGADO y CANCELADO)
            estados_data = self.uow.pedidos.get_pedidos_por_estado()
            pedidos_activos = sum(row.cantidad for row in estados_data if row.estado_codigo not in ['ENTREGADO', 'CANCELADO'])
            
            return ResumenResponse(
                ventas_hoy=ventas_hoy,
                ticket_promedio=ticket_promedio,
                pedidos_activos=pedidos_activos,
                ingresos_mes=ingresos_mes
            )
