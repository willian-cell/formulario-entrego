import sqlite3

DB_NAME = "entregadores.db"

def add_cnh_column():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(entregadores);")
    colunas = [c[1] for c in cursor.fetchall()]
    if "cnh" not in colunas:
        cursor.execute("ALTER TABLE entregadores ADD COLUMN cnh TEXT")
        conn.commit()
        print("✅ Coluna 'cnh' adicionada com sucesso.")
    else:
        print("ℹ️ Coluna 'cnh' já existe.")

    conn.close()

if __name__ == "__main__":
    add_cnh_column()
