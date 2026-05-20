import joblib
import io
import sys
try:
    import psycopg2
except ImportError:
    pass
from db import get_db_connection, release_db_connection

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(100) UNIQUE,
                model_data BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        print("ml_models database table schema verified/initialized.")
    except Exception as e:
        print(f"Failed to initialize database schema: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def save_model_to_db(model_path, model_name="random_forest_model"):
    conn = None
    try:
        with open(model_path, "rb") as f:
            model_binary = f.read()
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ml_models (model_name, model_data)
            VALUES (%s, %s)
            ON CONFLICT (model_name) 
            DO UPDATE SET model_data = EXCLUDED.model_data, created_at = CURRENT_TIMESTAMP;
        """, (model_name, psycopg2.Binary(model_binary)))
        
        conn.commit()
        cursor.close()
        print(f"Model '{model_name}' successfully saved to PostgreSQL database.")
        return True
    except Exception as e:
        print(f"Failed to save model to database: {e}")
        return False
    finally:
        if conn:
            release_db_connection(conn)

def load_model_from_db(model_name="random_forest_model"):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"Querying PostgreSQL for model '{model_name}'...")
        cursor.execute("SELECT model_data FROM ml_models WHERE model_name = %s;", (model_name,))
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            # Deserialize the binary data safely
            model_binary = result[0]
            if isinstance(model_binary, memoryview):
                model_binary = model_binary.tobytes()
            model_buffer = io.BytesIO(model_binary)
            
            # Use joblib to directly load from the BytesIO stream
            model = joblib.load(model_buffer)
            print(f"Model '{model_name}' successfully deserialized from PostgreSQL database.")
            return model
        else:
            print(f"Model '{model_name}' not found in the database.")
            return None
    except Exception as e:
        print(f"Failed to load model from database: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            release_db_connection(conn)
