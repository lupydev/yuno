"""
Script para limpiar y recrear la tabla normalized_payment_events

Este script elimina la tabla existente y todos sus tipos ENUM asociados,
y luego la recrea desde cero usando SQLModel.
"""

from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DB_DSN = "postgresql://postgres:OymPLdKHtAnAcRyRpjQyPhpCqHMjpsgv@maglev.proxy.rlwy.net:33322/railway"


def clean_database():
    """Elimina la tabla y los tipos ENUM existentes"""
    engine = create_engine(DB_DSN, echo=True)

    print("🧹 Cleaning existing database objects...")

    with engine.connect() as conn:
        # Eliminar la tabla si existe
        conn.execute(text("DROP TABLE IF EXISTS normalized_payment_events CASCADE;"))
        
        # Eliminar los tipos ENUM si existen
        conn.execute(text("DROP TYPE IF EXISTS paymentstatus CASCADE;"))
        conn.execute(text("DROP TYPE IF EXISTS failurereason CASCADE;"))
        conn.execute(text("DROP TYPE IF EXISTS normalizationmethod CASCADE;"))
        
        conn.commit()

    print("✅ Database cleaned successfully!")


if __name__ == "__main__":
    clean_database()
    print("\n✨ Now you can run: python normalized_db_injector.py")
