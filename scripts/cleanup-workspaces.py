#!/usr/bin/env python3
import os
import shutil
import sqlite3

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Locate DB
    db_path = os.getenv("DATABASE_PATH")
    if not db_path:
        db_path = os.path.join(repo_root, "apps", "api", "state.db")
    
    print(f"Using database: {db_path}")
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            # Fetch all workspace local paths before truncating
            try:
                cursor.execute("SELECT local_path FROM engineering_workspaces")
                paths = [row[0] for row in cursor.fetchall() if row[0]]
            except Exception as e:
                print(f"Could not fetch workspaces: {e}")
                paths = []
            
            # Delete directories
            for path in paths:
                if os.path.exists(path):
                    print(f"Deleting workspace directory: {path}")
                    try:
                        shutil.rmtree(path)
                    except Exception as e:
                        print(f"Error deleting {path}: {e}")
            
            # Truncate tables
            tables_to_truncate = ["engineering_workspaces", "agent_contexts", "chat_messages"]
            for table in tables_to_truncate:
                print(f"Truncating table: {table}")
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except Exception as e:
                    print(f"Error truncating table {table}: {e}")
            conn.commit()
            print("Database tables truncated successfully.")
        finally:
            conn.close()
    else:
        print("Database file does not exist, skipping database truncation.")
        
    # Also clean ~/workspace and ~/wright directories if they exist
    home_dir = os.path.expanduser("~")
    for parent_name in ["workspace", "wright"]:
        parent_dir = os.path.join(home_dir, parent_name)
        if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
            print(f"Cleaning subdirectories under: {parent_dir}")
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path) and not item.startswith("."):
                    print(f"Deleting directory: {item_path}")
                    try:
                        shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Error deleting {item_path}: {e}")

if __name__ == "__main__":
    main()
