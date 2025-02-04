from pydantic import BaseModel
from cat.mad_hatter.decorators import hook, plugin, tool
import os
import sqlite3


DB_DIR = None
DB_NAME = None
DB_PATH = None
conn = None

class Settings(BaseModel):
    dir: str = "/app/cat/plugins/chess-sql-plugin/db"  # File path for SQLite
    name: str = "chess"

@plugin
def settings_model():
    return Settings

@hook # default priority = 1
def after_cat_bootstrap(cat):
    # Ensure the directory exists (already handled in Docker configuration)
    # Connect to SQLite database (or create it if it doesn't exist)
    settings = cat.mad_hatter.get_plugin().load_settings()
    
    global DB_DIR
    global DB_NAME
    global DB_PATH
    global conn
    
    DB_DIR = settings.get('dir')
    DB_NAME = f"{settings.get('name')}.sqlite"
    DB_PATH = os.path.join(DB_DIR, DB_NAME)
    
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    # Create players table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        elo INTEGER NOT NULL,
        wins INTEGER NOT NULL DEFAULT 0,
        losses INTEGER NOT NULL DEFAULT 0,
        draws INTEGER NOT NULL DEFAULT 0
    );
    """
    
    cursor.execute(create_table_query)
    
    # Commit changes
    conn.commit()
    

@tool(return_direct=True)
def create_new_table(query, cat):
    """Query is the input and it is the query to create the table on SQLite."""
    
    global conn
    
    try :
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        return "**Table created successfully!**\n" + "```sql\n" + query + "\n```"
        
    except Exception as e:
        return str(e)