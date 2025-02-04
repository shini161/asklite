from pydantic import BaseModel
from cat.mad_hatter.decorators import hook, plugin, tool
import os
import sqlite3

DB_DIR = None
DB_NAME = None
DB_PATH = None
conn = None
db_structure = None

class DatabaseExecutionError(Exception):
    """Custom exception for handling database execution errors."""
    pass

class Settings(BaseModel):
    dir: str = "/app/cat/plugins/asklite/db"  # File path for SQLite
    name: str = "base"

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
 
    update_db_structure()
    
@hook
def agent_prompt_prefix(prefix, cat):
    prefix = f"""
    This is current db structure:
    {db_structure}
    """

    return prefix
    

@tool(return_direct=True)
def create_new_table(query, cat):
    """Query is the input and it is the query to create the table on SQLite."""
    
    global conn
    
    try :
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        update_db_structure()
        
        return "**Table created successfully!**\n" + "```sql\n" + query + "\n```"
        
    except Exception as e:
        return str(e)
    
@tool(return_direct=True)
def delete_table(query, cat):
    """Query is the input and it is the query to delete the table from SQLite."""
    
    global conn
    
    try :
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        
        update_db_structure()
        
        return "**Table deleted successfully!**\n" + "```sql\n" + query + "\n```"
        
    except Exception as e:
        return str(e)

@tool(return_direct=True)
def update_table(query, cat):
    """Query is the input and it is the query to update the table on SQLite.
    SQLite does not support changing column type or dropping column, 
    so update the name of the old table to "[name]_temp", then create directly a new table  with the new final structure and 
    copy the data from the old table to the new one, then drop the old 
    table and rename the new table to the name of the previous table"""
    
    global conn
    
    try :   
        execute_multiple_statements(conn, query)
        update_db_structure()
        
        return "**Table updated successfully!**\n" + "```sql\n" + query + "\n```"
        
    except Exception as e:
        return str(e)
    
@tool(return_direct=True)
def get_db_structure(query, cat):
    """What's database structure? query is input and is not used, can be ignored, just pass empty string."""

    global db_structure
    if db_structure:
        # Replace the double line breaks between tables with <br> for better spacing
        formatted_structure = db_structure.replace("\n\n", "<br><br>")
        return formatted_structure
    else:
        return "No structure available."


def update_db_structure():
    """Updates the db_structure by fetching the current schema of the database."""
    global db_structure
    global conn
    
    cursor = conn.cursor()

    # Fetch the structure of all tables in the database, excluding sqlite_sequence
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = cursor.fetchall()

    db_structure = ""
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Add table structure to db_structure
        db_structure += f"{table_name} table:\n"
        for col in columns:
            db_structure += f"- {col[1]} ({col[2]})\n"
        
        # Add a line break between tables
        db_structure += "\n\n"  # Two line breaks for extra space between tables


def execute_multiple_statements(conn, query):
    # Split the query at ';' to separate multiple statements
    statements = query.split(';')
    
    # Remove any empty strings resulting from split (in case of trailing semicolons)
    statements = [stmt.strip() for stmt in statements if stmt.strip()]
    
    cursor = conn.cursor()
    
    # Execute each statement separately
    for statement in statements:
        try:
            cursor.execute(statement)
            conn.commit()
        except sqlite3.Error as e:
            # Raise a custom exception with a detailed error message
            raise DatabaseExecutionError(f"Error executing statement: {statement}\nError: {e}")