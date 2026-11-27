import datetime
import logging
import os
import sqlite3
import threading
import psutil

from speedview.config.config import CONFIG_FILE


def format_bytes(num_bytes):
    """Format byte count into human-readable string."""
    val = max(0.0, float(num_bytes or 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if val < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(val)} B"
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{int(num_bytes)} B"


class DataUsageTracker:
    """Tracks real per-app, daily, and monthly network data usage in SQLite."""

    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(CONFIG_FILE)
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "data_usage.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_usage (
                        date TEXT NOT NULL,
                        month TEXT NOT NULL,
                        app_name TEXT NOT NULL,
                        bytes_recv INTEGER NOT NULL DEFAULT 0,
                        bytes_sent INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (date, app_name)
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def _get_active_network_apps(self):
        """Return {app_name: weight} for processes currently holding active inet sockets."""
        weights = {}
        try:
            conns = psutil.net_connections(kind="inet")
        except Exception as e:
            logging.debug(f"Could not inspect net_connections: {e}")
            return weights

        pid_names = {}
        for conn in conns:
            if not conn.pid:
                continue
            status = getattr(conn, "status", "")
            # Prefer active/established sockets and ignore pure loopback listeners
            if status == "LISTEN":
                continue
            laddr_ip = getattr(conn.laddr, "ip", "") if conn.laddr else ""
            raddr_ip = getattr(conn.raddr, "ip", "") if conn.raddr else ""
            if raddr_ip.startswith("127.") or raddr_ip == "::1":
                continue
            if not conn.raddr and (laddr_ip.startswith("127.") or laddr_ip == "::1"):
                continue

            if conn.pid not in pid_names:
                try:
                    pid_names[conn.pid] = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pid_names[conn.pid] = None

            name = pid_names[conn.pid]
            if name:
                weights[name] = weights.get(name, 0) + 1

        return weights

    def record_traffic(self, delta_recv, delta_sent, now=None):
        """Attribute real interface byte deltas across active networked apps and persist to SQLite."""
        delta_recv = max(0, int(delta_recv or 0))
        delta_sent = max(0, int(delta_sent or 0))
        if delta_recv == 0 and delta_sent == 0:
            return

        dt = now or datetime.datetime.now()
        date_str = dt.strftime("%Y-%m-%d")
        month_str = dt.strftime("%Y-%m")

        app_weights = self._get_active_network_apps()
        if not app_weights:
            app_weights = {"System / Network": 1}

        total_weight = sum(app_weights.values())
        allocations = []
        rem_recv = delta_recv
        rem_sent = delta_sent
        items = list(app_weights.items())
        for idx, (app_name, weight) in enumerate(items):
            if idx == len(items) - 1:
                r = rem_recv
                s = rem_sent
            else:
                r = (delta_recv * weight) // total_weight
                s = (delta_sent * weight) // total_weight
                rem_recv -= r
                rem_sent -= s
            if r > 0 or s > 0:
                allocations.append((date_str, month_str, app_name, r, s))

        if not allocations:
            return

        with self._lock:
            conn = self._connect()
            try:
                conn.executemany(
                    """
                    INSERT INTO app_usage (date, month, app_name, bytes_recv, bytes_sent)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(date, app_name) DO UPDATE SET
                        bytes_recv = bytes_recv + excluded.bytes_recv,
                        bytes_sent = bytes_sent + excluded.bytes_sent
                    """,
                    allocations,
                )
                conn.commit()
            finally:
                conn.close()

    def get_daily_usage(self, date_str=None):
        """Return (total_bytes, rows) for a given day (defaults to today)."""
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """
                    SELECT app_name, bytes_recv, bytes_sent, (bytes_recv + bytes_sent) AS total_bytes, date
                    FROM app_usage
                    WHERE date = ?
                    ORDER BY total_bytes DESC
                    """,
                    (date_str,),
                )
                rows = [
                    {
                        "app": row[0],
                        "bytes_recv": row[1],
                        "bytes_sent": row[2],
                        "bytes": row[3],
                        "date": row[4],
                    }
                    for row in cur.fetchall()
                ]
            finally:
                conn.close()

        total_bytes = sum(r["bytes"] for r in rows)
        return total_bytes, rows

    def get_monthly_usage(self, month_str=None):
        """Return (total_bytes, rows) for a given month YYYY-MM (defaults to current month)."""
        if month_str is None:
            month_str = datetime.datetime.now().strftime("%Y-%m")

        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """
                    SELECT app_name,
                           SUM(bytes_recv) AS recv_sum,
                           SUM(bytes_sent) AS sent_sum,
                           SUM(bytes_recv + bytes_sent) AS total_bytes,
                           MAX(date) AS latest_date
                    FROM app_usage
                    WHERE month = ?
                    GROUP BY app_name
                    ORDER BY total_bytes DESC
                    """,
                    (month_str,),
                )
                rows = [
                    {
                        "app": row[0],
                        "bytes_recv": row[1],
                        "bytes_sent": row[2],
                        "bytes": row[3],
                        "date": row[4],
                    }
                    for row in cur.fetchall()
                ]
            finally:
                conn.close()

        total_bytes = sum(r["bytes"] for r in rows)
        return total_bytes, rows

    def clear_usage(self):
        """Clear stored usage history."""
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM app_usage")
                conn.commit()
            finally:
                conn.close()
