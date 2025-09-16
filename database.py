import sqlite3

def setup_database():
    """Configura la base de datos y las tablas."""
    conn = sqlite3.connect('sistema_promotoras.db')
    cursor = conn.cursor()

    # Tabla para el emisor del informe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emisor (
            nombre TEXT PRIMARY KEY
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO emisor (nombre) VALUES (?)", ('NAYLEN JIMENEZ',))

    # Tabla para promotoras con los datos estandarizados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promotoras (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            inventario_inicial INTEGER,
            unidades_por_caja INTEGER,
            comercio TEXT
        )
    ''')
    
    # Tabla para las ventas diarias, solo con fecha y cantidad de combos
    # Se añade la restricción UNIQUE(promotora_id, fecha)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY,
            fecha TEXT,
            combos_vendidos INTEGER,
            promotora_id INTEGER,
            UNIQUE(promotora_id, fecha),
            FOREIGN KEY (promotora_id) REFERENCES promotoras(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos configurada exitosamente.")

if __name__ == '__main__':
    setup_database()
