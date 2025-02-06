from pydantic import BaseModel
from cat.mad_hatter.decorators import hook, plugin, tool
from cat.experimental.form import CatForm, CatFormState, form
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any

DB_DIR = None
DB_NAME = None
DB_PATH = None
conn = None
db_structure = None
db_structure_last_update_date = None

table_class_map: Dict[str, Any] = {}

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
    
    _init(cat)
    
@hook
def activated(cat):
    # Ensure the directory exists (already handled in Docker configuration)
    # Connect to SQLite database (or create it if it doesn't exist)
    # After plugin is activated
    
    _init(cat)

    
@hook
def agent_prompt_prefix(prefix, cat):
    if datetime.now() - db_structure_last_update_date > timedelta(minutes=1):
        update_db_structure()
    
    prefix = f"""
    This is current db structure:
    {db_structure}
    """

    return prefix
 
@tool(return_direct=True)
def create_table(query, cat):
    """Query is the input and it is the queries to create the tables on SQLite."""
    
    global conn
    
    try :
        execute_multiple_statements(conn, query)
        update_db_structure()
        
        return "**Table created successfully!**\n" + "```sql\n" + query + "\n```"
        
    except Exception as e:
        return str(e)
    
@tool(return_direct=True)
def delete_table(query, cat):
    """Query is the input and it is the queries to delete the tables from SQLite."""
    
    global conn
    
    try :
        execute_multiple_statements(conn, query)
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
    """Updates the db_structure and dynamically generates Pydantic models with table_name as the first field."""
    global db_structure, db_structure_last_update_date, table_class_map, conn

    cursor = conn.cursor()

    # Fetch the structure of all tables in the database (excluding sqlite_sequence)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = cursor.fetchall()

    db_structure = ""
    table_class_map.clear()  # Reset class mappings

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Store the structure
        db_structure += f"{table_name} table:\n"
        
        attributes = {
            "__annotations__": {"table_name": str}  # Ensure table_name is the first field
        }

        for col in columns:
            col_name, col_type = col[1], col[2]
            db_structure += f"- {col_name} ({col_type})\n"
            
            # Convert SQLite types to Python types
            python_type = (
                int if "INT" in col_type.upper() else 
                float if "REAL" in col_type.upper() else 
                str  # Default to string
            )
            attributes["__annotations__"][col_name] = python_type

        db_structure += "\n\n"

        # Create a Pydantic model dynamically
        model = type(
            table_name.capitalize(),  # Class name
            (BaseModel,),  # Inheriting from Pydantic's BaseModel
            attributes
        )

        # Store model in dictionary
        table_class_map[table_name] = model

    db_structure_last_update_date = datetime.now()

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
        
@tool
def get_settings(query, cat):
    """Get the current settings for the plugin."""
    settings = cat.mad_hatter.get_plugin().load_settings()
    
    try:
        return f"Settings:\n{settings}"
    except Exception as e:
        return str(e)
        
def _init(cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    
    global DB_DIR
    global DB_NAME
    global DB_PATH
    global conn
    
    if (DB_DIR and DB_NAME and DB_PATH and conn):
        return
    
    DB_DIR = settings.get('dir')
    DB_NAME = f"{settings.get('name')}.sqlite"
    DB_PATH = os.path.join(DB_DIR, DB_NAME)
    
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    
    update_db_structure()