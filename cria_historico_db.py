import sqlite3

# Conectar (ou criar) banco
conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

# Criar a tabela se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        sessao_id TEXT,
        assunto TEXT,
        modelo TEXT,
        pergunta TEXT,
        resposta TEXT
    )
''')

conn.commit()
conn.close()

print("Banco de dados chat_history.db criado com sucesso!")