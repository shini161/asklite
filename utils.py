from pydantic import BaseModel
from datetime import datetime
import sqlite3
import cat.plugins.asklite.vars as vars

class DatabaseExecutionError(Exception):
    """Custom exception for handling database execution errors."""
    pass

def update_db_structure():
    """Updates the db_structure and dynamically generates Pydantic models with only insertable fields and foreign key detection."""
    
    cursor = vars.conn.cursor()

    # Fetch the structure of all tables in the database (excluding sqlite_sequence)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = cursor.fetchall()

    vars.db_structure = ""
    vars.table_class_map.clear()  # Reset class mappings
    table_names = []

    for table in tables:
        table_name = table[0]
        table_names.append(table_name)
        
        # Get table columns
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        foreign_keys = cursor.fetchall()
        fk_map = {fk[3]: fk[2] for fk in foreign_keys}  # {column_name: referenced_table}

        # Store the structure
        vars.db_structure += f"{table_name} table:\n"
        
        attributes = {
            "__annotations__": {"table_name": str}  # Ensure table_name is the first field
        }

        for col in columns:
            col_name, col_type, notnull, default, pk = col[1], col[2], col[3], col[4], col[5]
            
            # Exclude auto-incrementing primary key fields
            if pk == 1 and "INT" in col_type.upper():
                continue
            
            # Check if column is a foreign key
            relation_info = f" -> {fk_map[col_name]}" if col_name in fk_map else ""

            vars.db_structure += f"- {col_name} ({col_type}){relation_info}\n"
            
            # Convert SQLite types to Python types
            python_type = (
                int if "INT" in col_type.upper() else 
                float if "REAL" in col_type.upper() else 
                str  # Default to string
            )
            attributes["__annotations__"][col_name] = python_type

        vars.db_structure += "\n\n"

        # Create a Pydantic model dynamically
        model = type(
            table_name.capitalize(),  # Class name
            (BaseModel,),  # Inheriting from Pydantic's BaseModel
            attributes
        )

        # Store model in dictionary
        vars.table_class_map[table_name] = model

    vars.table_names_str = f"Table names are: {', '.join(table_names)}"
    vars.db_structure_last_update_date = datetime.now()


def execute_multiple_statements(query):
    # Split the query at ';' to separate multiple statements
    statements = query.split(';')
    
    # Remove any empty strings resulting from split (in case of trailing semicolons)
    statements = [stmt.strip() for stmt in statements if stmt.strip()]
    
    cursor = vars.conn.cursor()
    
    # Execute each statement separately
    for statement in statements:
        try:
            cursor.execute(statement)
            vars.conn.commit()
        except sqlite3.Error as e:
            # Raise a custom exception with a detailed error message
            raise DatabaseExecutionError(f"Error executing statement: {statement}\nError: {e}")