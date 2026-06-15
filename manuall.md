# 7. Patrón Unit of Work (UoW)

El Unit of Work actúa como director de orquesta que garantiza que todas las operaciones de base de datos dentro de una transacción de negocio tengan éxito o fallen como un conjunto. El commit ocurre en el UoW, no en el service. Las notificaciones WebSocket se emiten DESPUÉS del commit exitoso, fuera del bloque UoW.

## 7.1 Flujo de una Operación con UoW — Crear Pedido

*Figura 4 — Flujo de creación de pedido con Unit of Work. Todos los INSERT son atómicos.*

| Paso | Capa | Operación | ¿Toca BD? |
| --- | --- | --- | --- |
| 1 | Router | Recibe POST `/api/v1/pedidos`. Valida body con `CrearPedidoRequest`. | No |
| 2 | Router | Abre contexto: `with UnitOfWork() as uow:` — llama `service.crear_pedido(uow, body, usuario_id)`. | No |
| 3 | Service | Itera items. Para cada uno: `uow.productos.get_by_id()`. Verifica disponible = true. | Lectura |
| 4 | Service | Calcula subtotal, descuento (si aplica) y total = subtotal - descuento + costo_envio. | No |
| 5 | Service | Llama `uow.pedidos.create(pedido)`. `uow.flush()` → obtiene `pedido.id`. | INSERT + flush |
| 6 | Service | Crea `DetallePedido` por cada item con `nombre_snapshot`, `precio_snapshot`, `subtotal_snap`. | INSERT × N |
| 7 | Service | Crea primer `HistorialEstadoPedido` con `estado_desde=None` (RN-02). | INSERT |
| 8 | UoW | `__exit__` sin excepción → `session.commit()`. Todo persiste atómicamente. | COMMIT |
| 9 | Router | Serializa pedido con `PedidoRead.model_validate(pedido)`. Retorna HTTP 201. | No |
| ERR | UoW | Si cualquier paso 3-7 lanza excepción → `__exit__` llama `rollback()`. Nada persiste. | ROLLBACK |

## 7.2 Flujo Avanzar Estado con WebSocket

*Figura 5 — Flujo de avanzar_estado con UoW + notificación WebSocket post-commit.*

| Paso | Capa | Operación | ¿Toca BD/WS? |
| --- | --- | --- | --- |
| 1 | Router | Recibe PATCH `/pedidos/{id}/estado`. Valida `AvanzarEstadoRequest`. | No |
| 2 | Service | Dentro de `with UoW() as uow:` — obtiene pedido, valida FSM. | Lectura |
| 3 | Service | UPDATE `Pedido.estado_codigo` = nuevo_estado. | UPDATE |
| 4 | Service | INSERT `HistorialEstadoPedido` con `estado_desde`, `estado_hacia`, `usuario_id`, `motivo`. | INSERT |
| 5 | UoW | `__exit__` sin excepción → `session.commit()`. Cambio de estado persiste. | COMMIT |
| 6 | Service | FUERA del bloque UoW: `await ws_manager.broadcast_pedido(pedido_id, evento)` | WebSocket |
| 7 | WSManager | Itera conexiones activas para `pedido_id` y canal `/ws/admin/pedidos`. Envía JSON. | WS Send |
| 8 | Router | Serializa `PedidoRead` y retorna HTTP 200. | No |

## 7.3 BaseRepository[T] Genérico

| Método | Descripción |
| --- | --- |
| `get_by_id(entity_id: int) -> T \| None` | Obtiene entidad por clave primaria. Retorna None si no existe. |
| `list_all(skip: int, limit: int) -> list[T]` | Listado simple sin filtros. |
| `count() -> int` | Cantidad total de registros. Útil para paginación. |
| `create(entity: T) -> T` | Agrega a sesión + `flush()` + `refresh()`. Retorna entidad con ID asignado. |
| `update(entity: T) -> T` | Agrega entidad modificada a sesión + `flush()` + `refresh()`. |
| `soft_delete(entity: T) -> None` | Asigna `deleted_at = now()`. Solo para entidades con soft-delete. |
| `hard_delete(entity: T) -> None` | Hard delete. Solo se usa cuando el modelo no tiene soft-delete. |

# 11. Módulo Estadísticas

El módulo de estadísticas provee KPIs y métricas del negocio exclusivamente al rol ADMIN. Todas las consultas son de solo lectura y se ejecutan contra las tablas existentes del modelo (Pedido, DetallePedido, Pago, Producto). No requiere nuevas tablas ni migraciones adicionales. Los datos son consumidos por los gráficos recharts del panel de administración.

## 11.1 Estructura del Módulo

| Archivo | Responsabilidad |
| --- | --- |
| `app/modules/estadisticas/router.py` | Define los endpoints GET `/api/v1/estadisticas/*`. Sin lógica, delega al service. |
| `app/modules/estadisticas/service.py` | Lógica de cálculo de KPIs. Llama a los repositorys. |
| `app/modules/estadisticas/schemas.py` | Schemas Pydantic: `ResumenResponse`, `VentasPeriodoItem`, `ProductoTopItem`, `PedidosEstadoItem`, `IngresosResponse`. |

## 11.2 Queries Clave — Repository

| Método | Notas |
| --- | --- |
| `get_ventas_periodo(desde, hasta, agrupacion)` | Usa `DATE_TRUNC` de PostgreSQL. agrupacion puede ser 'day', 'week', 'month'. |
| `get_productos_top(limit)` | Usa `subtotal_snap` (snapshot inmutable) para ingresos precisos. |
| `get_pedidos_por_estado()` | Simple GROUP BY sobre el estado actual de cada pedido. |
| `get_resumen_kpis()` | Cada KPI es una query separada. El service ensambla el `ResumenResponse`. |
| `get_ingresos_por_forma_pago(desde, hasta)` | Solo pedidos con pago aprobado. Forma de pago desde `Pedido.forma_pago_codigo`. |

## 11.3 Visualización Frontend — recharts

| Gráfico | Endpoint consumido | Componente recharts | Datos mapeados |
| --- | --- | --- | --- |
| Ventas por período | GET `/estadisticas/ventas` | LineChart + Line | eje X: periodo, eje Y: total_ventas y cantidad_pedidos (dos líneas) |
| Top productos | GET `/estadisticas/productos-top` | BarChart + Bar | eje X: nombre (truncado), eje Y: ingresos. Tooltip: cantidad_vendida. |
| Distribución por estado | GET `/estadisticas/pedidos-por-estado` | PieChart + Pie | name: estado_codigo, value: cantidad. Cell con color por estado. |
| Ingresos por forma de pago | GET `/estadisticas/ingresos` | BarChart horizontal | eje Y: forma_pago_codigo, eje X: total. Muestra cantidad en tooltip. |
| KPIs cards | GET `/estadisticas/resumen` | StatCard custom | 4 cards: ventas hoy, ticket promedio, pedidos activos, mes actual. |

> **Reglas de negocio — Estadísticas:**
> *   **EST-01:** Nunca incluir pedidos con `estado_codigo = CANCELADO` en cálculos de ingresos o cantidades vendidas.
> *   **EST-02:** Usar `subtotal_snap` de `DetallePedido` para ingresos por producto (garantiza precios históricos correctos).
> *   **EST-03:** Solo contar pagos con `mp_status = 'approved'` al calcular ingresos confirmados.
> *   **EST-04:** Todos los montos devueltos deben ser `DECIMAL(10,2)`. Nunca float nativo Python para dinero.
> *   **EST-05:** Las queries de período aceptan desde y hasta como date (no datetime). El filtro usa BETWEEN.

# 13. Tests con TestClient

Food Store utiliza pytest con el TestClient de FastAPI (basado en httpx) para tests de integración de los endpoints REST y WebSocket. Los tests cubren los flujos críticos: autenticación, ciclo de vida de pedidos, pagos, estadísticas y WebSocket.

## 13.1 Configuración — conftest.py

| Fixture | Scope | Descripción |
| --- | --- | --- |
| `engine` | session | Crea motor SQLite en memoria o PostgreSQL de test. Aplica `create_all()`. Se descarta al final de la sesión. |
| `db_session` | function | Session de SQLAlchemy limpia para cada test. Hace rollback automático al finalizar cada test. |
| `client` | function | TestClient de FastAPI. Sobreescribe la dependency `get_db` con `db_session`. |
| `admin_headers` | function | Loguea un usuario ADMIN. Retorna Cookie. |
| `client_headers` | function | Loguea un usuario CLIENT. Retorna Cookie. |
| `pedidos_headers` | function | Loguea un usuario PEDIDOS. Retorna Cookie. |
| `producto_factory` | function | Crea un Producto con stock disponible en la BD de test. |
| `pedido_factory` | function | Crea un Pedido en estado PENDIENTE con un DetallePedido. Acepta usuario_id y producto_id. |

> **Estrategia de base de datos en tests:** SQLite in-memory para velocidad.

## 13.2 Estructura de Archivos de Test

| Archivo | Módulo testeado | Tests principales |
| --- | --- | --- |
| `tests/conftest.py` | — | Fixtures globales: engine, db_session, client, factories, headers. |
| `tests/test_auth.py` | auth | register OK, login OK, login credenciales inválidas (401), refresh token, logout + revocación, rate limit (429). |
| `tests/test_pedidos.py` | pedidos | crear pedido OK, stock insuficiente (400), avanzar estado válido, avanzar estado inválido (422), cancelar propio, historial append-only. |
| `tests/test_estadisticas.py` | estadisticas | resumen OK, ventas por período, productos top, pedidos por estado, ingresos (solo approved). Verifica que CANCELADO no suma. |

## 13.3 Patrones de Test por Módulo

| Módulo | Patrón de test | Qué verificar |
| --- | --- | --- |
| Auth | Arrange: crear usuario. Act: POST `/auth/login`. Assert: status 200, access_token en body, refresh_token en body. | Token válido, `token_type='bearer'`, expiración en `expires_in`. |
| Pedidos FSM | Arrange: crear pedido en PENDIENTE. Act: PATCH `/pedidos/{id}/estado` con CONFIRMADO. Assert: 200, `estado_codigo='CONFIRMADO'`. | Transición válida actualiza estado. Historial append-only tiene nuevo registro. |
| Pedidos FSM (inválido) | Arrange: pedido en ENTREGADO (terminal). Act: PATCH `/pedidos/{id}/estado` con EN_PREP. Assert: 422. | RN-01: estado terminal rechaza transiciones. |
| Estadísticas | Arrange: crear N pedidos con distintos estados y productos. Act: GET `/estadisticas/resumen`. Assert: `ventas_hoy > 0`, CANCELADO excluido. | EST-01/EST-02/EST-03 validadas en tests de integración. |