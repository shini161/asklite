from cat.mad_hatter.decorators import tool  # type: ignore
from cat.mad_hatter.decorators import hook  # type: ignore
from cat.experimental.form import CatForm, CatFormState, form  # type: ignore
from pydantic import BaseModel  # type: ignore
import os
import sqlite3

# Path to the database file
DB_DIR = "/app/cat/plugins/chess/db"
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "chess.db")

@hook
def after_cat_bootstrap(cat):
    # Ensure the directory exists (already handled in Docker configuration)
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # SQL command to create a table if it doesn't exist
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

    # Execute the SQL command
    cursor.execute(create_table_query)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

@hook
def agent_prompt_prefix(prefix, cat):
    prefix = """You are a SQL query writer. You can add players to a database and retrieve their stats. If there's a tool output, you must return that output."""

    return prefix

@tool
def populate_database(query, cat):
    """This tool is used to insert many players to the table 'players'. 
    If the number of players to insert is not provided, it will insert 10 players.
    max number of players to insert is 25.
    query is the input and the sql query string to insert the players.
    The fields are name, elo, wins, losses, and draws.
    name's must be unique.
    elo, wins, losses, and draws are integers, can be randomly generated."""

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # check if query is empty
        if not query:
            return "Something went wrong."
        
        # Execute the SQL query
        cursor.execute(query)
        conn.commit()
    
        return "**Players were added successfully**"
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return {"output": "Error: A player with the same name already exists."}
        return {"output": "Error: " + str(e)}
    finally:
        conn.close()
    
@tool
def get_stat_avg(query, cat):
    """Get the average [stat] of players <filter>.
    <filter> is "WHERE [condition]", and is used to filter the players to get the average [stat] of.
    [stat] can be 'elo', 'wins', 'losses', or 'draws'.
    query is the input and is "[stat name]\n[sql query string]<filter>" string to get the average [stat]. 
    Replace [stat name] with the name of the stat you want to get the average of. 
    Replace [sql query string] with the sql query string to get the average [stat].
    If no filter is passed replace <filter> with ""
    """

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stat_name = query.split("\n")[0]
        query = query.split("\n")[1]

        # Execute the SQL query
        cursor.execute(query)
        average_elo = cursor.fetchone()[0]

        return f"The average {stat_name} is {average_elo}"
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()
        
@tool
def get_max_stat(query, cat):
    """Get max [stat] of players <filter>.
    <filter> is "WHERE [condition]", and is used to filter the players to get the max [stat] of.
    [stat] can be 'elo', 'wins', 'losses', or 'draws'.
    query is the input and is "[stat name]\n[sql query string]<filter>" string to get the max [stat]. 
    Replace [stat name] with the name of the stat you want to get the max of. 
    Replace [sql query string] with the sql query string to get the max [stat].
    If no filter is passed replace <filter> with ""
    """

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stat_name = query.split("\n")[0]
        query = query.split("\n")[1]

        # Execute the SQL query
        cursor.execute(query)
        max_elo = cursor.fetchone()[0]

        return f"Return: \"The max {stat_name} of [criteria] is **{max_elo}**\"\nReplace [criteria] with the criteria to get the max {stat_name} of."
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()
        
@tool
def get_min_stat(query, cat):
    """Get min [stat] of players <filter>.
    <filter> is "WHERE [condition]", and is used to filter the players to get the min [stat] of.
    [stat] can be 'elo', 'wins', 'losses', or 'draws'.
    query is the input and is "[stat name]\n[sql query string]<filter>" string to get the min [stat]. 
    Replace [stat name] with the name of the stat you want to get the min of. 
    Replace [sql query string] with the sql query string to get the min [stat].
    If no filter is passed replace <filter> with ""
    """

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        stat_name = query.split("\n")[0]
        query = query.split("\n")[1]

        # Execute the SQL query
        cursor.execute(query)
        min_elo = cursor.fetchone()[0]

        return f"Return: \"The min {stat_name} of players [criteria] is **{min_elo}**\"\nReplace [criteria] with the criteria to get the min {stat_name} of."
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()
        
@tool
def clear_database(query, cat):
    """Clear the table 'players' in the database.
    query is the input and is the sql query string to clear the table 'players'."""

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(query)
        conn.commit()

        return "Database cleared successfully"
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()

# FIX ME (doesnt get called)
@tool
def get_players_by_filter(query, cat):
    """Get first [count] players by <filter>.
    Default value for <count> is 10.
    Max value for [count] is 25.
    <filter> is "WHERE [condition]", and is used to filter the players to get.
    query is the input and is "[title]\n[sql query string]<filter>" string to get the players.
    Replace [title] with "Top [count] players by <filter>" where [count] is the number of players and <filter> is the <filter> to sort by.
    Replace [sql query string] with the sql query string to get the players.
    If no filter is passed replace <filter> with ""
    Table name 'players', fields are name, elo, wins, losses, and draws."""
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        count = query.split("\n")[0]
        query = query.split("\n")[1]

        # Execute the SQL query
        cursor.execute(query)
        players = cursor.fetchall()

        if not players:
            return "No players found."

        player_list = [count + "\n"]
        for player in players:
            player_list.append(f"Name: {player[1]}\nElo: {player[2]}\nWins: {player[3]}\nLosses: {player[4]}\nDraws: {player[5]}\n")

        return player_list
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()
    

@tool
def get_player_count(query, cat):
    """Get the number of players in the database.
    query is the input and is the sql query string to get the number of players."""

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(query)
        player_count = cursor.fetchone()[0]

        return f"The number of players in the database is {player_count}"
    except Exception as e:
        return "Error: " + str(e)
    finally:
        conn.close()


class ChessPlayer(BaseModel):
    name: str
    elo: int
    wins: int
    losses: int
    draws: int


@form
class ChessPlayerFormInsert(CatForm):
    description = "Chess Player Form"
    model_class = ChessPlayer
    start_examples = [
        "insert a player",
        "add a player",
        "new chess player",
    ]
    stop_examples = [
        "stop adding players",
        "no more players",
    ]
    ask_confirm = True

    def submit(self, form_data):
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
                # Check if a player with the same name already exists
            cursor.execute("SELECT id FROM players WHERE name = ?", (form_data["name"],))
            existing_player = cursor.fetchone()

            if existing_player:
                return {"output": f"Player with name '{form_data['name']}' already exists."}


            # Insert player data
            query_string = (
                f"INSERT INTO players (name, elo, wins, losses, draws) "
                f"VALUES ('{form_data['name']}', {form_data['elo']}, {form_data['wins']}, "
                f"{form_data['losses']}, {form_data['draws']});"
            )

            cursor.execute(query_string)
            conn.commit()

            return {
                "output": f"```sql\n{query_string}\n```\n**Player added successfully**"
            }
        except Exception as e:
            return {"output": "Error: " + str(e)}
        finally:
            conn.close()


@tool
def get_player_data(name, cat):
    """Get chess stats. name is the input"""

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM players WHERE name = ?;", (name,))
        player_data = cursor.fetchone()

        if player_data is None:
            return "No data found for " + name
        else:
            return "Name: {}\nElo: {}\nWins: {}\nLosses: {}\nDraws: {}".format(
                player_data[1], player_data[2], player_data[3], player_data[4], player_data[5]
            )
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()
