"""
Seed principal. Ejecutar: python seed_all.py
Crea en orden: roles → admin → estados → formas de pago → categorías → ingredientes → productos
"""
from decimal import Decimal
from sqlmodel import Session, select, SQLModel

from app.core.database import engine
from app.core.security import hash_password
from app.modules.dominio_1.usuario.models import Usuario, Rol
from app.modules.dominio_2.categoria.models import Categoria
from app.modules.dominio_2.ingrediente.models import Ingrediente
from app.modules.dominio_2.producto.models import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.dominio_2.UnidadMedida.models import UnidadMedida
from app.modules.dominio_3.EstadoPedido.models import EstadoPedido
from app.modules.dominio_3.FormaPago.models import FormaPago
from app.modules.dominio_3.Pedido.models import Pedido  # noqa: F401
from app.modules.dominio_3.DetallePedido.models import DetallePedido  # noqa: F401
from app.modules.dominio_3.HistorialEstadoPedido.models import HistorialEstadoPedido  # noqa: F401


def seed():
    print("--- INICIANDO SEED ---")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:

        # ══════════════════════════════════════════════════════
        # DOMINIO 1 — Roles y usuario admin
        # ══════════════════════════════════════════════════════

        roles_necesarios = [
            {"codigo": "ADMIN",   "nombre": "Administrador",    "descripcion": "Acceso total sin restricciones"},
            {"codigo": "STOCK",   "nombre": "Gestor de Stock",   "descripcion": "Actualiza stock y disponible"},
            {"codigo": "PEDIDOS", "nombre": "Gestor de Pedidos", "descripcion": "Avanza estados CONFIRMADO->ENTREGADO"},
            {"codigo": "CLIENT",  "nombre": "Cliente",           "descripcion": "Opera solo sus propios datos"},
            {"codigo": "COCINA",  "nombre": "Cocina",            "descripcion": "Recibe pedidos para preparar"},
        ]
        roles_db = {}
        for rol_data in roles_necesarios:
            rol = session.exec(select(Rol).where(Rol.codigo == rol_data["codigo"])).first()
            if not rol:
                print(f"  Creando rol: {rol_data['codigo']}")
                rol = Rol(**rol_data)
                session.add(rol)
            roles_db[rol_data["codigo"]] = rol
        session.commit()

        email_admin = "admin@foodstore.com"
        admin = session.exec(select(Usuario).where(Usuario.email == email_admin)).first()
        if not admin:
            print("  Creando usuario ADMIN...")
            nuevo_admin = Usuario(
                nombre="Super",
                apellido="Admin",
                email=email_admin,
                celular="2611234567",
                password_hash=hash_password("admin123"),
            )
            nuevo_admin.roles.append(roles_db["ADMIN"])
            session.add(nuevo_admin)
            session.commit()
            print("  ✅ Admin creado (admin@foodstore.com / admin123)")
        else:
            print("  ✅ Admin ya existe, se omite.")

        email_cliente = "cliente@foodstore.com"
        cliente_prueba = session.exec(select(Usuario).where(Usuario.email == email_cliente)).first()
        if not cliente_prueba:
            print("  Creando usuario CLIENTE de prueba...")
            nuevo_cliente = Usuario(
                nombre="Cliente",
                apellido="Prueba",
                email=email_cliente,
                celular="2610000000",
                password_hash=hash_password("cliente123"), # Misma función que usaste arriba
            )
            nuevo_cliente.roles.append(roles_db["CLIENT"]) # Le damos el rol de cliente
            session.add(nuevo_cliente)
            session.commit()
            print("  ✅ Cliente creado (cliente@foodstore.com / cliente123) - ID: 2")
        else:
            print("  ✅ Cliente de prueba ya existe, se omite.")

        # ══════════════════════════════════════════════════════
        # DOMINIO 3 — Estados de pedido y formas de pago
        # ══════════════════════════════════════════════════════

        estados = [
            {"codigo": "PENDIENTE",  "descripcion": "Pedido ingresado y pendiente de confirmación", "orden": 1,  "es_terminal": False},
            {"codigo": "CONFIRMADO", "descripcion": "Pedido confirmado por el comercio",             "orden": 2,  "es_terminal": False},
            {"codigo": "EN_PREP",    "descripcion": "Pedido en preparación",                         "orden": 3,  "es_terminal": False},
            {"codigo": "EN_CAMINO",  "descripcion": "Pedido en camino al cliente",                   "orden": 4,  "es_terminal": False},
            {"codigo": "ENTREGADO",  "descripcion": "Pedido entregado exitosamente",                 "orden": 5,  "es_terminal": True},
            {"codigo": "CANCELADO",  "descripcion": "Pedido cancelado",                              "orden": 99, "es_terminal": True},
        ]
        for est_data in estados:
            est = session.exec(select(EstadoPedido).where(EstadoPedido.codigo == est_data["codigo"])).first()
            if not est:
                print(f"  Creando estado: {est_data['codigo']}")
                session.add(EstadoPedido(**est_data))

        formas_pago = [
            {"codigo": "EFECTIVO",    "descripcion": "Pago en Efectivo",                "habilitado": True},
            {"codigo": "MERCADOPAGO", "descripcion": "Mercado Pago (QR/Transferencia)", "habilitado": True},
            {"codigo": "TARJETA",     "descripcion": "Tarjeta de Crédito / Débito",     "habilitado": True},
        ]
        for fp_data in formas_pago:
            fp = session.exec(select(FormaPago).where(FormaPago.codigo == fp_data["codigo"])).first()
            if not fp:
                print(f"  Creando forma de pago: {fp_data['codigo']}")
                session.add(FormaPago(**fp_data))
        session.commit()

        # ══════════════════════════════════════════════════════
        # DOMINIO 2 — Categorías, ingredientes y productos
        # ══════════════════════════════════════════════════════

        # ── Categorías principales ────────────────────────────
        hamburguesas = Categoria(nombre="Hamburguesas", descripcion="Nuestras burgers artesanales", imagen_url="https://via.placeholder.com/400x300?text=Hamburguesas")
        bebidas      = Categoria(nombre="Bebidas",      descripcion="Frías y calientes",            imagen_url="https://via.placeholder.com/400x300?text=Bebidas")
        postres      = Categoria(nombre="Postres",      descripcion="Para cerrar con dulzura",       imagen_url="https://via.placeholder.com/400x300?text=Postres")
        session.add_all([hamburguesas, bebidas, postres])
        session.flush()

        # ── Subcategorías ─────────────────────────────────────
        veganas  = Categoria(nombre="Veganas",   descripcion="100% plant-based",   imagen_url="https://via.placeholder.com/400x300?text=Veganas",  parent_id=hamburguesas.id)
        sin_tacc = Categoria(nombre="Sin TACC",  descripcion="Libres de gluten",   imagen_url="https://via.placeholder.com/400x300?text=SinTACC",  parent_id=hamburguesas.id)
        gaseosas = Categoria(nombre="Gaseosas",  descripcion="Bebidas con gas",    imagen_url="https://via.placeholder.com/400x300?text=Gaseosas", parent_id=bebidas.id)
        session.add_all([veganas, sin_tacc, gaseosas])
        session.flush()

        # ── Ingredientes ──────────────────────────────────────
        pan_brioche  = Ingrediente(nombre="Pan Brioche",          descripcion="Pan suave y esponjoso",    es_alergeno=True)
        pan_sin_tacc = Ingrediente(nombre="Pan Sin TACC",         descripcion="Pan libre de gluten",       es_alergeno=False)
        carne_250    = Ingrediente(nombre="Carne Vacuna 250g",    descripcion="Medallón de res premium",   es_alergeno=False)
        medallon_veg = Ingrediente(nombre="Medallón Vegano",      descripcion="Base de legumbres y avena", es_alergeno=False)
        queso_ch     = Ingrediente(nombre="Queso Cheddar",        descripcion="Cheddar fundido americano", es_alergeno=True)
        queso_veg    = Ingrediente(nombre="Queso Vegano",         descripcion="Alternativa plant-based",   es_alergeno=False)
        lechuga      = Ingrediente(nombre="Lechuga",              descripcion="Lechuga fresca",            es_alergeno=False)
        tomate       = Ingrediente(nombre="Tomate",               descripcion="Tomate perita en rodajas",  es_alergeno=False)
        cebolla_c    = Ingrediente(nombre="Cebolla Caramelizada", descripcion="Cebolla dulce",             es_alergeno=False)
        bacon        = Ingrediente(nombre="Bacon Crocante",       descripcion="Panceta ahumada",           es_alergeno=False)
        salsa_bbq    = Ingrediente(nombre="Salsa BBQ",            descripcion="Salsa ahumada casera",      es_alergeno=False)
        mayonesa     = Ingrediente(nombre="Mayonesa",             descripcion="Mayo artesanal",            es_alergeno=True)
        session.add_all([pan_brioche, pan_sin_tacc, carne_250, medallon_veg, queso_ch, queso_veg, lechuga, tomate, cebolla_c, bacon, salsa_bbq, mayonesa])
        session.flush()

        # ── Unidades de medida ────────────────────────────────
        unidades = [
            {"nombre": "Kilogramo",      "simbolo": "kg",  "tipo": "peso"},
            {"nombre": "Gramo",          "simbolo": "g",   "tipo": "peso"},
            {"nombre": "Litro",          "simbolo": "L",   "tipo": "volumen"},
            {"nombre": "Mililitro",      "simbolo": "mL",  "tipo": "volumen"},
            {"nombre": "Unidad",         "simbolo": "u",   "tipo": "unidad"},
            {"nombre": "Docena",         "simbolo": "doc", "tipo": "unidad"},
            {"nombre": "Metro cuadrado", "simbolo": "m²",  "tipo": "superficie"},
        ]
        for u in unidades:
            if not session.exec(select(UnidadMedida).where(UnidadMedida.simbolo == u["simbolo"])).first():
                session.add(UnidadMedida(**u))
        session.flush()

        # ── Productos ─────────────────────────────────────────
        clasica       = Producto(nombre="Hamburguesa Clásica", descripcion="La de siempre, perfecta de siempre.",    precio_base=Decimal("1500.00"), imagenes_url=["https://via.placeholder.com/400x300?text=Clasica"],  stock_cantidad=50)
        bbq           = Producto(nombre="Burger BBQ Bacon",    descripcion="Ahumada, crocante y con todo.",           precio_base=Decimal("1900.00"), imagenes_url=["https://via.placeholder.com/400x300?text=BBQ"],      stock_cantidad=30)
        vegana_prod   = Producto(nombre="Burger Vegana",       descripcion="Plant-based sin culpa.",                  precio_base=Decimal("1800.00"), imagenes_url=["https://via.placeholder.com/400x300?text=Vegana"],   stock_cantidad=25)
        sin_tacc_prod = Producto(nombre="Burger Sin TACC",     descripcion="Para celíacos, sin sacrificar sabor.",    precio_base=Decimal("1700.00"), imagenes_url=["https://via.placeholder.com/400x300?text=SinTACC"], stock_cantidad=20)
        coca          = Producto(nombre="Coca-Cola 500ml",     descripcion="La clásica bien fría.",                   precio_base=Decimal("800.00"),  stock_cantidad=100)
        limonada      = Producto(nombre="Limonada Natural",    descripcion="Exprimida al momento.",                   precio_base=Decimal("700.00"),  stock_cantidad=60)
        session.add_all([clasica, bbq, vegana_prod, sin_tacc_prod, coca, limonada])
        session.flush()

        # ── Producto ↔ Categoría ──────────────────────────────
        session.add(ProductoCategoria(producto_id=clasica.id,       categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=bbq.id,           categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=vegana_prod.id,   categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=vegana_prod.id,   categoria_id=veganas.id,      es_principal=False))
        session.add(ProductoCategoria(producto_id=sin_tacc_prod.id, categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=sin_tacc_prod.id, categoria_id=sin_tacc.id,     es_principal=False))
        session.add(ProductoCategoria(producto_id=coca.id,          categoria_id=bebidas.id,      es_principal=True))
        session.add(ProductoCategoria(producto_id=coca.id,          categoria_id=gaseosas.id,     es_principal=False))
        session.add(ProductoCategoria(producto_id=limonada.id,      categoria_id=bebidas.id,      es_principal=True))

        # ── Producto ↔ Ingrediente ────────────────────────────
        # Clásica
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=pan_brioche.id, es_removible=False))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=carne_250.id,   es_removible=False))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=queso_ch.id,    es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=lechuga.id,     es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=tomate.id,      es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=mayonesa.id,    es_removible=True))
        # BBQ
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=pan_brioche.id, es_removible=False))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=carne_250.id,   es_removible=False))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=bacon.id,       es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=queso_ch.id,    es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=cebolla_c.id,   es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=salsa_bbq.id,   es_removible=True))
        # Vegana
        session.add(ProductoIngrediente(producto_id=vegana_prod.id, ingrediente_id=pan_brioche.id,  es_removible=False))
        session.add(ProductoIngrediente(producto_id=vegana_prod.id, ingrediente_id=medallon_veg.id, es_removible=False))
        session.add(ProductoIngrediente(producto_id=vegana_prod.id, ingrediente_id=queso_veg.id,    es_removible=True))
        session.add(ProductoIngrediente(producto_id=vegana_prod.id, ingrediente_id=lechuga.id,      es_removible=True))
        session.add(ProductoIngrediente(producto_id=vegana_prod.id, ingrediente_id=tomate.id,       es_removible=True))
        # Sin TACC
        session.add(ProductoIngrediente(producto_id=sin_tacc_prod.id, ingrediente_id=pan_sin_tacc.id, es_removible=False))
        session.add(ProductoIngrediente(producto_id=sin_tacc_prod.id, ingrediente_id=carne_250.id,    es_removible=False))
        session.add(ProductoIngrediente(producto_id=sin_tacc_prod.id, ingrediente_id=queso_ch.id,     es_removible=True))
        session.add(ProductoIngrediente(producto_id=sin_tacc_prod.id, ingrediente_id=lechuga.id,      es_removible=True))
        session.add(ProductoIngrediente(producto_id=sin_tacc_prod.id, ingrediente_id=tomate.id,       es_removible=True))

        session.commit()

    print("--- SEED FINALIZADO ✅ ---")
    print("   • 4 roles + usuario admin")
    print("   • 6 estados de pedido + 3 formas de pago")
    print("   • 6 categorías + 12 ingredientes + 7 unidades de medida + 6 productos")


if __name__ == "__main__":
    seed()