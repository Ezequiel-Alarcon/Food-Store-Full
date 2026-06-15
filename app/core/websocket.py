import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("app.core.websocket")


class ConnectionManager:
    """Gestor de conexiones WebSocket"""

    def __init__(self) -> None:
        """Inicializa el gestor de conexiones."""
        # Set de conexiones activas. Se usa set para evitar duplicados.
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Acepta el handshake y registra la conexion."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(
            f"Nueva conexion WebSocket: {len(self.active_connections)} total")

    def disconnect(self, websocket: WebSocket) -> None:
        """ Elimina la conexion del registro. Discard no lanza error si no existe"""
        self.active_connections.discard(websocket)
        logger.info(
            f"Conexion WebSocket cerrada: {len(self.active_connections)} total")

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """ 
        Envía un evento JSON a todas las pantallas KDS conectadas.
        Si una conexión falla, la remueve y continúa con las demás. 
        """
        payload = {
            "event": event_type,
            "data": data
        }

        if not self.active_connections:
            logger.info(f"Evento {event_type}: No hay pantallas conectadas")
            return

        logger.info(
            f"Transmitiendo evento {event_type} a {len(self.active_connections)} pantallas")
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception as e:
                # Conexión caída — la removemos y seguimos
                logger.warning(
                    f"Error al enviar WebSocket. Removiendo conexión: {e}")
                self.active_connections.discard(connection)


# Instancia global (singleton) del gestor de conexiones


manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Obtiene el gestor de conexiones WebSocket"""
    return manager
