import json
import os
import sqlite3
from contextlib import contextmanager
from enum import StrEnum

from loguru import logger

from .models import Message, User


class OrderBy(StrEnum):
    ASC = "ASC"
    DES = "DESC"


class UserNotFound(Exception): ...


class DBService:
    def __init__(self, db_url: str):
        self.db_url = db_url

    @contextmanager
    def connect(self):
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect(self.db_url)
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def create_db(self) -> None:
        # Define the SQL command to create the "messages" table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            ogmessage_id INTEGER PRIMARY KEY,
            replymessage_jump_url TEXT,
            replymessage_id INTEGER,
            author_id INTEGER,
            channel_id INTEGER,
            guild_id INTEGER,
            roundness REAL,
            labels_json TEXT
        )
        """

        create_usertable_sql = """
        CREATE TABLE IF NOT EXISTS discordusers (
            author_id INTEGER PRIMARY KEY,
            author_nickname TEXT,
            author_name TEXT
        ) ;  
        """
        os.makedirs(os.path.dirname(self.db_url), exist_ok=True)
        with self.connect() as cursor:
            # Execute the SQL command
            cursor.execute(create_table_sql)
            cursor.execute(create_usertable_sql)

    def upsert_message_stats(
        self, ogmessage_id: int, roundness: float, labels_json: dict
    ) -> None:
        logger.info(f"Upserting: {ogmessage_id}, {roundness}, {labels_json} in messages")
        labels_json_str = json.dumps(labels_json)

        upsert_sql = """
        INSERT INTO messages (ogmessage_id, roundness, labels_json)
        VALUES (?, ?, ?)
        ON CONFLICT(ogmessage_id) DO UPDATE SET
            roundness=excluded.roundness,
            labels_json=excluded.labels_json
        """

        with self.connect() as cursor:
            cursor.execute(upsert_sql, (ogmessage_id, roundness, labels_json_str))

    def upsert_user_info(self, user: User) -> None:
        # Inserts the author info to cache results so we don't have to get info from discord all the time
        logger.info(
            f"Upserting: {user.author_id}, {user.author_nickname}, {user.author_name} in discordusers"
        )
        # Convert the labels_json dictionary to a JSON string
        # Define the UPSERT SQL command
        upsert_sql = """
        INSERT INTO discordusers (author_id, author_nickname, author_name)
        VALUES (?, ?, ?)
        ON CONFLICT(author_id) DO UPDATE SET
            author_nickname=excluded.author_nickname,
            author_name=excluded.author_name
        """

        with self.connect() as cursor:
            cursor.execute(
                upsert_sql, (user.author_id, user.author_nickname, user.author_name)
            )

    def select_user_info(self, author_id: int) -> User:
        logger.trace(f"Getting user info from {author_id}")
        select_sql = "SELECT author_id, author_nickname, author_name FROM discordusers WHERE author_id = ?"
        with self.connect() as cursor:
            cursor.execute(select_sql, (author_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    author_id=row[0],
                    author_nickname=row[1],
                    author_name=row[2],
                )
            raise UserNotFound()

    def upsert_message_discordinfo(
        self,
        ogmessage_id: int,
        replymessage_jump_url: str,
        replymessage_id: int,
        author_id: int,
        channel_id: int,
        guild_id: int,
    ) -> None:
        logger.info(
            f"Upserting: {ogmessage_id}, {replymessage_jump_url}, {replymessage_id}, {author_id}, {channel_id}, {guild_id}"
        )
        upsert_sql = """
        INSERT INTO messages (ogmessage_id, replymessage_jump_url, replymessage_id, author_id, channel_id, guild_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(ogmessage_id) DO UPDATE SET
            replymessage_jump_url=excluded.replymessage_jump_url,
            replymessage_id=excluded.replymessage_id,
            author_id=excluded.author_id,
            channel_id=excluded.channel_id,
            guild_id=excluded.guild_id
        """

        with self.connect() as cursor:
            cursor.execute(
                upsert_sql,
                (
                    ogmessage_id,
                    replymessage_jump_url,
                    replymessage_id,
                    author_id,
                    channel_id,
                    guild_id,
                ),
            )

    def get_min_roundness_for_user(self, user_id: int) -> Message:
        return self._get_roundness_message_byuserid(user_id, OrderBy.ASC)

    def get_max_roundness_for_user(self, user_id: int) -> Message:
        return self._get_roundness_message_byuserid(user_id, OrderBy.DES)

    def _get_roundness_message_byuserid(self, user_id: int, orderby: OrderBy) -> Message:
        logger.info(f"Fetching roundness for user_id: {user_id}")

        query = f"""
        {Message.select()}
        WHERE author_id = ?
        AND roundness NOT NULL
        ORDER BY roundness {orderby.value}, ogmessage_id {orderby.value}
        LIMIT 1
        """
        with self.connect() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            if rows:
                return Message.from_row(rows[0])
        raise UserNotFound()

    def get_max_roundness_leaderboard(self, n: int) -> list[Message]:
        return self._get_minmax_roundness_leaderboard(n, OrderBy.DES)

    def get_min_roundness_leaderboard(self, n: int) -> list[Message]:
        return self._get_minmax_roundness_leaderboard(n, OrderBy.ASC)

    def _get_minmax_roundness_leaderboard(self, n: int, orderby: OrderBy) -> list[Message]:
        """Returns top 'n' min and max roundness returning the ogmessage_id and jump_url as well for each row"""
        logger.info(f"Fetching min and max roundness top {n} leaderboard")
        roundness_query = f"""
        {Message.select()}
        WHERE roundness not null
        ORDER BY roundness {orderby}
        LIMIT ?
        """
        result = []
        with self.connect() as cursor:
            cursor.execute(roundness_query, (n,))
            rows = cursor.fetchall()
            for row in rows:
                result.append(Message.from_row(row))
        return result

    def get_roundness_history(self, user_id: int) -> list[tuple[int, int]]:
        # Returns the roundness history for the user
        logger.info(f"Fetching  roundness of user {user_id}")
        roundness_query = f"""
        {Message.select()}
        WHERE 1=1
        AND roundness not null
        AND author_id = ?
        ORDER BY ogmessage_id {OrderBy.DES.value}
        LIMIT 50
        """
        result = []
        with self.connect() as cursor:
            cursor.execute(roundness_query, (user_id,))
            rows = cursor.fetchall()
            for i, row in enumerate(rows, start=1):
                message = Message.from_row(row)
                result.append((i, message.roundness))
        return result
