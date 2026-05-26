"""
Script de seed para desarrollo.
Ejecutar: python seed.py
Crea datos de prueba para demostrar el flujo completo del Dominio 3.
"""
from decimal import Decimal
from sqlmodel import Session, SQLModel, select
from app.core.database import engine
from app.modules.dominio_2.categoria.models import Categoria
from app.modules.dominio_2.ingrediente.models import Ingrediente
from app.modules.dominio_2.producto.models import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.dominio_2.UnidadMedida.models import UnidadMedida


def seed():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:

        # ── Unidades de medida ────────────────────────────────────────────────
        unidades_medida_seed = [
            {"nombre": "Kilogramo", "simbolo": "kg", "tipo": "peso"},
            {"nombre": "Gramo", "simbolo": "g", "tipo": "peso"},
            {"nombre": "Litro", "simbolo": "L", "tipo": "volumen"},
            {"nombre": "Mililitro", "simbolo": "mL", "tipo": "volumen"},
            {"nombre": "Unidad", "simbolo": "u", "tipo": "unidad"},
            {"nombre": "Docena", "simbolo": "doc", "tipo": "unidad"},
            {"nombre": "Metro cuadrado", "simbolo": "m²", "tipo": "superficie"},
        ]
        for unidad_data in unidades_medida_seed:
            existente = session.exec(select(UnidadMedida).where(UnidadMedida.simbolo == unidad_data["simbolo"])).first()
            if not existente:
                session.add(UnidadMedida(**unidad_data))
        session.flush()

        unidad = session.exec(select(UnidadMedida).where(UnidadMedida.simbolo == "u")).first()
        if not unidad:
            raise RuntimeError("No se encontró la unidad de medida 'u'")

        # ── CATEGORÍAS PRINCIPALES ───────────────────────────────────
        hamburguesas = Categoria(
            nombre="Hamburguesas",
            descripcion="Nuestras burgers artesanales",
            imagen_url="https://via.placeholder.com/400x300?text=Hamburguesas",
        )
        bebidas = Categoria(
            nombre="Bebidas",
            descripcion="Frías y calientes",
            imagen_url="https://via.placeholder.com/400x300?text=Bebidas",
        )
        postres = Categoria(
            nombre="Postres",
            descripcion="Para cerrar con dulzura",
            imagen_url="https://via.placeholder.com/400x300?text=Postres",
        )
        session.add_all([hamburguesas, bebidas, postres])
        session.flush()

        # ── SUBCATEGORÍAS ────────────────────────────────────────────
        veganas = Categoria(
            nombre="Veganas",
            descripcion="100% plant-based",
            imagen_url="https://via.placeholder.com/400x300?text=Veganas",
            parent_id=hamburguesas.id,
        )
        sin_tacc = Categoria(
            nombre="Sin TACC",
            descripcion="Libres de gluten",
            imagen_url="https://via.placeholder.com/400x300?text=SinTACC",
            parent_id=hamburguesas.id,
        )
        gaseosas = Categoria(
            nombre="Gaseosas",
            descripcion="Bebidas con gas",
            imagen_url="https://via.placeholder.com/400x300?text=Gaseosas",
            parent_id=bebidas.id,
        )
        session.add_all([veganas, sin_tacc, gaseosas])
        session.flush()

        # ── INGREDIENTES ─────────────────────────────────────────────
        pan_brioche  = Ingrediente(nombre="Pan Brioche",          descripcion="Pan suave y esponjoso",      es_alergeno=True)
        pan_sin_tacc = Ingrediente(nombre="Pan Sin TACC",         descripcion="Pan libre de gluten",         es_alergeno=False)
        carne_250    = Ingrediente(nombre="Carne Vacuna 250g",    descripcion="Medallón de res premium",     es_alergeno=False)
        medallon_veg = Ingrediente(nombre="Medallón Vegano",      descripcion="Base de legumbres y avena",   es_alergeno=False)
        queso_ch     = Ingrediente(nombre="Queso Cheddar",        descripcion="Cheddar fundido americano",   es_alergeno=True)
        queso_veg    = Ingrediente(nombre="Queso Vegano",         descripcion="Alternativa plant-based",     es_alergeno=False)
        lechuga      = Ingrediente(nombre="Lechuga",              descripcion="Lechuga fresca",              es_alergeno=False)
        tomate       = Ingrediente(nombre="Tomate",               descripcion="Tomate perita en rodajas",    es_alergeno=False)
        cebolla_c    = Ingrediente(nombre="Cebolla Caramelizada", descripcion="Cebolla dulce",               es_alergeno=False)
        bacon        = Ingrediente(nombre="Bacon Crocante",       descripcion="Panceta ahumada",             es_alergeno=False)
        salsa_bbq    = Ingrediente(nombre="Salsa BBQ",            descripcion="Salsa ahumada casera",        es_alergeno=False)
        mayonesa     = Ingrediente(nombre="Mayonesa",             descripcion="Mayo artesanal",              es_alergeno=True)
        session.add_all([
            pan_brioche, pan_sin_tacc, carne_250, medallon_veg,
            queso_ch, queso_veg, lechuga, tomate,
            cebolla_c, bacon, salsa_bbq, mayonesa,
        ])
        session.flush()

        # ── PRODUCTOS ────────────────────────────────────────────────
        clasica = Producto(
            nombre="Hamburguesa Clásica",
            descripcion="La de siempre, perfecta de siempre.",
            precio_base=Decimal("1500.00"),
            imagenes_url=["https://via.placeholder.com/400x300?text=Clasica"],
            stock_cantidad=50,
            unidad_venta_id=unidad.id,
        )
        bbq = Producto(
            nombre="Burger BBQ Bacon",
            descripcion="Ahumada, crocante y con todo.",
            precio_base=Decimal("1900.00"),
            imagenes_url=["https://via.placeholder.com/400x300?text=BBQ"],
            stock_cantidad=30,
            unidad_venta_id=unidad.id,
        )
        vegana_prod = Producto(
            nombre="Burger Vegana",
            descripcion="Plant-based sin culpa.",
            precio_base=Decimal("1800.00"),
            imagenes_url=["https://via.placeholder.com/400x300?text=Vegana"],
            stock_cantidad=25,
            unidad_venta_id=unidad.id,
        )
        sin_tacc_prod = Producto(
            nombre="Burger Sin TACC",
            descripcion="Para celíacos, sin sacrificar sabor.",
            precio_base=Decimal("1700.00"),
            imagenes_url=["https://via.placeholder.com/400x300?text=SinTACC"],
            stock_cantidad=20,
            unidad_venta_id=unidad.id,
        )
        coca = Producto(
            nombre="Coca-Cola 500ml",
            descripcion="La clásica bien fría.",
            precio_base=Decimal("800.00"),
            stock_cantidad=100,
            unidad_venta_id=unidad.id,
        )
        limonada = Producto(
            nombre="Limonada Natural",
            descripcion="Exprimida al momento.",
            precio_base=Decimal("700.00"),
            stock_cantidad=60,
            unidad_venta_id=unidad.id,
        )
        session.add_all([clasica, bbq, vegana_prod, sin_tacc_prod, coca, limonada])
        session.flush()


        # ── PRODUCTO ↔ CATEGORÍA ─────────────────────────────────────
        session.add(ProductoCategoria(producto_id=clasica.id,       categoria_id=hamburguesas.id, es_principal=True))

        session.add(ProductoCategoria(producto_id=bbq.id,           categoria_id=hamburguesas.id, es_principal=True))

        session.add(ProductoCategoria(producto_id=vegana_prod.id,   categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=vegana_prod.id,   categoria_id=veganas.id,      es_principal=False))

        session.add(ProductoCategoria(producto_id=sin_tacc_prod.id, categoria_id=hamburguesas.id, es_principal=True))
        session.add(ProductoCategoria(producto_id=sin_tacc_prod.id, categoria_id=sin_tacc.id,     es_principal=False))

        session.add(ProductoCategoria(producto_id=coca.id,          categoria_id=bebidas.id,      es_principal=True))
        session.add(ProductoCategoria(producto_id=coca.id,          categoria_id=gaseosas.id,     es_principal=False))

        session.add(ProductoCategoria(producto_id=limonada.id,      categoria_id=bebidas.id,      es_principal=True))

        # ── PRODUCTO ↔ INGREDIENTE ───────────────────────────────────
        # Clásica
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=pan_brioche.id, es_removible=False))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=carne_250.id,   es_removible=False))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=queso_ch.id,    es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=lechuga.id,     es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=tomate.id,      es_removible=True))
        session.add(ProductoIngrediente(producto_id=clasica.id, ingrediente_id=mayonesa.id,    es_removible=True))

        # BBQ Bacon
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=pan_brioche.id,  es_removible=False))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=carne_250.id,    es_removible=False))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=bacon.id,        es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=queso_ch.id,     es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=cebolla_c.id,    es_removible=True))
        session.add(ProductoIngrediente(producto_id=bbq.id, ingrediente_id=salsa_bbq.id,    es_removible=True))

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
        print("🌱 Seed OK:")
        print(f"   • 6 categorías (3 principales + 3 subcategorías)")
        print(f"   • 12 ingredientes (3 alérgenos)")
        print(f"   • 7 unidades de medida")
        print(f"   • 6 productos con categorías e ingredientes asignados")
        print(f"   • Relaciones con es_principal y es_removible configuradas")


if __name__ == "__main__":
    seed()
