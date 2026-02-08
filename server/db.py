import psycopg2
import os
import sqlite3

class DB:
    def __init__(self):
        try:
            check = False
            if os.path.exists(".env"):
                check = True
            from dotenv import load_dotenv; load_dotenv() if os.path.exists(".env") else None
            # if there is a proper env it uses PostgreSQL from .env
            if check:
                self.db = psycopg2.connect(
                    database=os.getenv("DATABASE"),
                    host=os.getenv("HOST"),
                    user=os.getenv("USER"),
                    password=os.getenv("PASSWORD"),
                    port=os.getenv("PORT"),
                    connect_timeout=3
                )
                self.db_type = "postgres"
            else:
                # yes there is a second fallback i could not get it to work otherwise
                self.db = sqlite3.connect(os.path.join(os.getcwd(), "wordle.db"), check_same_thread=False)
                self.db_type = "sqlite"
        except Exception:
            # but if its in development falls back to SQLite just for testing 
            self.db = sqlite3.connect(os.path.join(os.getcwd(), "wordle.db"), check_same_thread=False)
            self.db_type = "sqlite"
        
        self.create_table()
    
    # creates table (works with both)
    def create_table(self):
        query = """CREATE TABLE IF NOT EXISTS wins (
            username VARCHAR(255) PRIMARY KEY,
            wins INTEGER NOT NULL
        );"""
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
    
    # increase wins (with sepearete queries for both)
    def increase_wins(self, username):
        try:
            cursor = self.db.cursor()
            
            if self.db_type == "postgres":
                query = """
                INSERT INTO wins (username, wins) 
                VALUES (%s, 1)
                ON CONFLICT (username) 
                DO UPDATE SET wins = wins.wins + 1;
                """
                cursor.execute(query, (username,))
            else:  # sqlite
                query = """
                INSERT INTO wins (username, wins) 
                VALUES (?, 1)
                ON CONFLICT(username) 
                DO UPDATE SET wins = wins + 1;
                """
                cursor.execute(query, (username,))
            
            self.db.commit()
            cursor.close()
            
        except Exception as error:
            print(f"Error increasing wins: {error}")
            self.db.rollback()
            raise
    
    # gets stats (seperate queries for both)
    def get_user_stats(self, username):
        try:
            cursor = self.db.cursor()
            if self.db_type == "postgres":
                query = "SELECT wins FROM wins WHERE username = %s;"
                cursor.execute(query, (username,))
            else:  # sqlite
                query = "SELECT wins FROM wins WHERE username = ?;"
                cursor.execute(query, (username,))
            result = cursor.fetchone()
            if result is not None:
                return {'wins': result[0]}
            else:
                return {'wins': 0}
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting user stats: {error}")
            return {'wins': 0}
    
    # gets leaderboard
    def get_leaderboard(self):
        """Get top players by number of wins"""
        query = """
        SELECT username, wins
        FROM wins
        ORDER BY wins DESC
        LIMIT 10;
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
                
            return [
                {'username': row[0], 'wins': row[1]}
                for row in results
            ]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error fetching leaderboard: {error}")
            return []
    
    # close
    def close(self):
        if self.db:
            self.db.close()
    
    # delete
    def __del__(self):
        self.close()