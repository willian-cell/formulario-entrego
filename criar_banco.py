import sqlite3

# Nome do arquivo do banco
DB_NAME = "entregadores.db"

# Script SQL para criar a tabela
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS entregadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    email TEXT NOT NULL,
    tipo_chave_pix TEXT NOT NULL,
    chave_pix TEXT NOT NULL,
    validacao_chave_pix TEXT NOT NULL,
    nacionalidade TEXT NOT NULL,
    estado_civil TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    rg TEXT NOT NULL,
    data_nascimento DATE NOT NULL,
    cnpj TEXT,
    cidade TEXT NOT NULL,
    modal TEXT NOT NULL,
    foto_rosto TEXT,
    cnh TEXT
);
"""

def criar_banco(drop_existing=False):
    # Conectar ao banco (cria o arquivo se não existir)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if drop_existing:
        cursor.execute("DROP TABLE IF EXISTS entregadores;")
        print("⚠️ Tabela 'entregadores' antiga removida.")

    # Criar tabela
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados '{DB_NAME}' criado com sucesso com a tabela 'entregadores'.")

if __name__ == "__main__":
    # Passe drop_existing=True se quiser apagar a tabela antiga antes de criar
    criar_banco(drop_existing=True)
