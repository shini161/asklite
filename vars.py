from typing import Dict, Any

DB_DIR = None
DB_NAME = None
DB_PATH = None
conn = None
db_structure = None
db_structure_last_update_date = None
table_names_str = None
show_sql = False

table_class_map: Dict[str, Any] = {}