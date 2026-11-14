"""Shared SQLite storage for a single app server with a writable data directory."""
from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class ProgressChanged(Exception):
    """Another tab or device saved a newer version."""


class Storage:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.hasher = PasswordHasher(time_cost=2, memory_cost=32768)
        self.dummy = self.hasher.hash("unregistered")
        with self.connection() as db:
            db.execute("pragma journal_mode=WAL")
            db.executescript("""
                create table if not exists settings (
                    key text primary key, value blob not null
                );
                create table if not exists accounts (
                    username text primary key, display_name text not null,
                    password_hash text not null, xp integer not null default 0,
                    version integer not null default 0, progress text not null default '{}',
                    failed_attempts integer not null default 0, locked_until real not null default 0
                );
                create table if not exists login_limits (
                    client_key text primary key, window_started real not null, attempts integer not null
                );
                create table if not exists events (
                    id integer primary key, username text not null references accounts(username),
                    happened_at integer not null default (unixepoch()),
                    word_id integer not null, day_key text not null, stage integer not null,
                    kind text not null, xp integer not null, seconds integer not null
                );
                create index if not exists events_user_time on events(username, happened_at);
                create index if not exists rank_order on accounts(xp desc, username);
            """)
            db.execute("insert or ignore into settings values ('login_secret', ?)",
                       (secrets.token_bytes(32),))
            self.secret = db.execute("select value from settings where key='login_secret'").fetchone()[0]

    @contextmanager
    def connection(self, write=False):
        db = sqlite3.connect(self.path, timeout=8)
        db.row_factory = sqlite3.Row
        try:
            with db:
                db.execute("pragma foreign_keys=on")
                if write:
                    db.execute("begin immediate")
                yield db
        finally:
            db.close()

    def private_password(self, username, pin):
        return hmac.new(self.secret, (username + "\0" + pin).encode(), hashlib.sha256).hexdigest()

    def authenticate(self, username, display, pin, register, client):
        client_key = hmac.new(self.secret, client.encode(), hashlib.sha256).hexdigest()
        private = self.private_password(username, pin)
        now = time.time()
        with self.connection(write=True) as db:
            db.execute("delete from login_limits where window_started <= ?", (now-600,))
            db.execute("""
                insert into login_limits values (?, ?, 1)
                on conflict(client_key) do update set attempts=min(attempts+1,121)
            """, (client_key, now))
            attempts = db.execute("select attempts from login_limits where client_key=?",
                                  (client_key,)).fetchone()[0]
        if attempts > 120:
            return "limited"
        if register:
            hashed = self.hasher.hash(private)
            with self.connection(write=True) as db:
                row = db.execute("""
                    insert into accounts(username,display_name,password_hash)
                    values (?,?,?) on conflict(username) do nothing
                """, (username, display, hashed))
                return "ok" if row.rowcount else "exists"
        with self.connection(write=True) as db:
            row = db.execute("select * from accounts where username=?", (username,)).fetchone()
            if row and row["locked_until"] > now:
                return "invalid"
            try:
                self.hasher.verify(row["password_hash"] if row else self.dummy, private)
                matches = bool(row)
            except VerifyMismatchError:
                matches = False
            if not row:
                return "invalid"
            failures = 0 if matches else (0 if row["locked_until"] else row["failed_attempts"]) + 1
            db.execute("update accounts set failed_attempts=?,locked_until=? where username=?",
                       (failures, now+600 if failures >= 5 else 0, username))
            return "ok" if matches else "invalid"

    def load(self, username):
        with self.connection() as db:
            row = db.execute("select display_name,xp,version,progress from accounts where username=?",
                             (username,)).fetchone()
        return {**json.loads(row["progress"]), "name": row["display_name"],
                "xp": row["xp"], "version": row["version"]}

    def save(self, username, profile, event=None):
        payload = {k: v for k, v in profile.items() if k not in {"name", "xp", "version"}}
        earned = event[-2] if event else 0
        with self.connection(write=True) as db:
            updated = db.execute("""
                update accounts set progress=?,version=version+1,xp=xp+?
                where username=? and version=?
            """, (json.dumps(payload, ensure_ascii=False), earned, username, profile["version"]))
            if updated.rowcount != 1:
                raise ProgressChanged
            if event:
                db.execute("""
                    insert into events(username,word_id,day_key,stage,kind,xp,seconds)
                    values (?,?,?,?,?,?,?)
                """, (username, *event))
        profile["version"] += 1
        profile["xp"] += earned

    def ranking(self):
        with self.connection() as db:
            return db.execute("""
                select display_name,xp from accounts where xp>0 order by xp desc,username
            """).fetchall()

    def events(self, username):
        with self.connection() as db:
            daily = db.execute("""
                select date(happened_at,'unixepoch','+9 hours') as day,
                    sum(seconds) as seconds,sum(xp) as xp,
                    sum(case when kind='incorrect' then 1 else 0 end) as wrong
                from events where username=?
                    and date(happened_at,'unixepoch','+9 hours') >= date('now','+9 hours','-30 days')
                group by day order by day
            """, (username,)).fetchall()
            summary = db.execute("""
                select day_key,stage,kind,count(*) as count,sum(seconds) as seconds
                from events where username=? group by day_key,stage,kind
            """, (username,)).fetchall()
        return daily, summary
