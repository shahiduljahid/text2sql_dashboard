#!/usr/bin/env python
"""
Database reset script for Student Management Text-to-SQL MVP.
Resets the database to clean demo state.
"""
import os
import sys

def reset_database():
    """Reset the database by removing and recreating it."""
    db_path = "student_management.db"

    print("Resetting database...")

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Creating new database...")
        # Run init script
        os.system(f"python init_database.py")
        return

    # Ask for confirmation
    print(f"WARNING: This will delete the existing database at {db_path}")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Reset cancelled.")
        return

    # Remove database and recreate
    try:
        os.remove(db_path)
        print("Database removed.")

        # Run init script
        print("Creating new database...")
        os.system(f"python init_database.py")

        print("\nDatabase reset complete!")

    except Exception as e:
        print(f"Error resetting database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()