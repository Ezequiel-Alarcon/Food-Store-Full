import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("app.core.websocket")


class ConnectionManager:
    """Gestor de conexiones WebSocket"""

    def __init__(self) -> None:
        """Inicializa el gestor de conexiones."""
        # Set de conexiones activas. Se usa set para evitar duplicados.
        # self.active_connections: set[WebSocket] = set()
        
        self.rooms: dict[str, set[WebSocket]] = {}
        self.socket_rooms: dict[WebSocket, set[str]] = {}
        
    def _join_room(self, websocket: WebSocket, room: str) -> None:
      if room not in self.rooms:
        self.rooms[room] = set()
        
      self.rooms[room].add(websocket)
      
      if websocket not in self.socket_rooms:
        self.socket_rooms[websocket] = set()
        
      self.socket_rooms[websocket].add(room)

    async def connect(self, websocket: WebSocket, role: str, user_id: int) -> None:
        """Acepta el handshake y registra la conexion."""
        await websocket.accept()
        
        """Normalizamos el rol a mayusculas para evitar inconsistencias"""
        #TODO: Validar role
        role_key = f"role:{role.upper()}"
        
        """Unimos el socket a su room de rol"""
        #TODO: El usuario debe tener un solo rol
        self._join_room(websocket, role_key)
        
        # self.active_connections.add(websocket)
        logger.info(
            f"Conexion Websocket aceptada. user_id={user_id}, role={role}, "
            f"room={role_key}. Total de rooms activas: {len(self.rooms)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Obtener y eliminar el mapa inverso"""
        rooms = self.socket_rooms.pop(websocket, set())
        
        """Rmover de cada room: O(r)"""
        for room in rooms:
          if room in self.rooms:
            self.rooms[room].discard(websocket)
            """Se elimina la room se queda vacia"""
            if not self.rooms[room]:
              del self.rooms[room]
        logger.info(
          f"Conexion Websocket finalizada. Rooms liberadas: {rooms}. "
          f"Total rooms activas: {len(self.rooms)}"
        )
        
    def join_role_room(self, websocket: WebSocket, role_code: str) -> None:
      room = f"role:{role_code.upper()}"
      self._join_room(websocket, room)
      logger.info(f"Socket suscrito a room {room}")
    
    def leave_role_room(self, websocket: WebSocket, role_code: str) -> None:
      room = f"role:{role_code.upper()}"
      if room in self.rooms:
        self.rooms[room].discard(websocket)
        if websocket in self.socket_rooms:
          self.socket_rooms[websocket].discard(room)
          
        if not self.rooms[room]:
          del self.rooms[room]

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
