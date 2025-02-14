from pydantic import BaseModel
from cat.mad_hatter.decorators import hook, plugin, tool
import os
import sqlite3
from datetime import datetime, timedelta
from cat.plugins.asklite.utils import update_db_structure, execute_multiple_statements
import cat.plugins.asklite.vars as vars

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
    if datetime.now() - vars.db_structure_last_update_date > timedelta(minutes=1):
        update_db_structure()
    
    prefix = f"""
    Database Used: SQLite
    \n\n
    Current db structure:
    {vars.db_structure}
    \n\n
    {vars.table_names_str}
    \n\n
    Table Outputs are to be formatted as markdowns tables.
    \n\nWhen asked to generate random values, be creative but simple
    \n\nShow SQL query used: {vars.show_sql}
    """

    return prefix

@tool(return_direct=True)
def toggle_sql(bool, cat):
    """Show the SQL query used in markdown code block? bool is the input and it is 'True' or 'False'."""
    
    if bool == "True":
        vars.show_sql = True
        return "**Show SQL query enabled!**"
    else:
        vars.show_sql = False
        return "**Show SQL query disabled!**"
    
@tool
def query(query, cat):
    """
    If a sql procedure needs to use a SELECT, or COUNT, or AVG, MIN, MAX
    Query the database. query is the input and it is the SQL query string to get data from SQLite.
    if the query is SELECT, the output will be formatted as markdown table.
    if the query is INSERT, ignore
    if a size is asked, use COUNT(*) to get the number of items in the table.
    """
    
    try :
        cursor = vars.conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        
        if not data:
            return "No data found."
        
        return f"{data}"
        
    except Exception as e:
        return str(e)
 
@tool(return_direct=True)
def create_table(query, cat):
    """Query is the input and it is the queries to create the tables on SQLite."""
    
    try :
        execute_multiple_statements(query)
        update_db_structure()
        
        output = "**Table created successfully!**"
        
        if vars.show_sql:
            output += "\n" + "```sql\n" + query + "\n```"
        
        return output
        
    except Exception as e:
        return str(e)
    
@tool(return_direct=True)
def delete_table(query, cat):
    """Query is the input and it is the queries to delete the tables from SQLite."""
    
    try :
        execute_multiple_statements(query)
        update_db_structure()
        
        output = "**Table deleted successfully!**"
        
        if vars.show_sql:
            output += "\n" + "```sql\n" + query + "\n```"
        
        return output
        
    except Exception as e:
        return str(e)

@tool(return_direct=True)
def update_table(query, cat):
    """Query is the input and it is the query to update the table on SQLite.
    SQLite does not support changing column type or dropping column, 
    so update the name of the old table to "[name]_temp", then create directly a new table  with the new final structure and 
    copy the data from the old table to the new one, then drop the old 
    table and rename the new table to the name of the previous table"""
    
    try :   
        execute_multiple_statements(query)
        update_db_structure()
        
        output = "**Table updated successfully!**"
        
        if vars.show_sql:
            output += "\n" + "```sql\n" + query + "\n```"
        
        return output
        
    except Exception as e:
        return str(e)
    
@tool(return_direct=True)
def get_db_structure(_, cat):
    """What's database structure?"""

    if vars.db_structure:
        # Replace the double line breaks between tables with <br> for better spacing
        formatted_structure = vars.db_structure.replace("\n\n", "<br><br>")
        return formatted_structure
    else:
        return "No structure available."
        
@tool
def get_settings(query, cat):
    """Get the current settings for the plugin."""
    settings = cat.mad_hatter.get_plugin().load_settings()
    2
    try:
        return f"Settings:\n{settings}"
    except Exception as e:
        return str(e)

@tool(return_direct=True)
def insert_data(query, cat):
    """
    Insert data to the table. query is the SQL query string to insert data to SQLite.
    """
    
    try :
        execute_multiple_statements(query)
        
        output = "**Data inserted successfully!**"
        
        if vars.show_sql:
            output += "\n" + "```sql\n" + query + "\n```"
        
        return output
        
    except Exception as e:
        return str(e)

def _init(cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    
    if (vars.DB_DIR and vars.DB_NAME and vars.DB_PATH and vars.conn):
        return
    
    vars.DB_DIR = settings.get('dir')
    vars.DB_NAME = f"{settings.get('name')}.sqlite"
    vars.DB_PATH = os.path.join(vars.DB_DIR, vars.DB_NAME)
    
    os.makedirs(vars.DB_DIR, exist_ok=True)
    
    vars.conn = sqlite3.connect(vars.DB_PATH, check_same_thread=False)
    
    update_db_structure()
    
