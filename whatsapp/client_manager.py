"""
server/whatsapp/client_manager.py — Multi-client orchestrator
"""
from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from dotenv import load_dotenv
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv
from rich.console import Console

from .connection import build_client, BOT_NAME

load_dotenv()
console = Console()


@dataclass
class ClientInstance:
    session_id: str
    client: Optional[NewClient] = None
    phone_number: str = ""
    status: str = "disconnected"
    thread: Optional[threading.Thread] = None
    pairing_enabled: bool = False
    pairing_phone: str = ""
    config: dict = field(default_factory=dict)


class ClientManager:
    """Manages multiple WhatsApp client instances."""

    def __init__(self):
        self._clients: Dict[str, ClientInstance] = {}
        self._message_callbacks: list[Callable] = []
        self._status_callbacks: list[Callable] = []
        self._lock = threading.Lock()

    @property
    def active_sessions(self) -> list[str]:
        with self._lock:
            return list(self._clients.keys())

    def get_client(self, session_id: str) -> Optional[NewClient]:
        with self._lock:
            instance = self._clients.get(session_id)
            return instance.client if instance else None

    def get_instance(self, session_id: str) -> Optional[ClientInstance]:
        with self._lock:
            return self._clients.get(session_id)

    def get_status(self, session_id: str) -> str:
        instance = self.get_instance(session_id)
        return instance.status if instance else "not_found"

    def register_existing(self, session_id: str, client: NewClient, phone_number: str = "", pairing_enabled: bool = False, pairing_phone: str = ""):
        """Register an already-running client with the manager."""
        with self._lock:
            instance = ClientInstance(
                session_id=session_id,
                client=client,
                phone_number=phone_number,
                status="connected",
                pairing_enabled=pairing_enabled,
                pairing_phone=pairing_phone,
            )
            self._clients[session_id] = instance
            console.print(f"[green]✓ Registered existing client: {session_id}[/green]")
        return instance

    def on_message(self, callback: Callable):
        self._message_callbacks.append(callback)

    def on_status_change(self, callback: Callable):
        self._status_callbacks.append(callback)

    def create_client(
        self, session_id: str, session_name: str = None, db_path: str = None,
        phone_number: str = "", pairing_enabled: bool = False, pairing_phone: str = "",
    ) -> ClientInstance:
        with self._lock:
            if session_id in self._clients:
                return self._clients[session_id]

            if db_path:
                sessions_dir = os.path.dirname(os.path.abspath(db_path))
                if sessions_dir and not os.path.exists(sessions_dir):
                    os.makedirs(sessions_dir, exist_ok=True)

            client = build_client(
                session_name=session_name or session_id, db_path=db_path,
                on_message_callback=lambda cli, msg: self._handle_message(cli, msg, session_id),
                on_connected_callback=lambda cli, ev: self._on_connected(session_id),
                on_pair_callback=lambda cli, ev: self._on_pair(session_id, ev),
            )

            instance = ClientInstance(
                session_id=session_id, client=client, phone_number=phone_number,
                status="disconnected", pairing_enabled=pairing_enabled,
                pairing_phone=pairing_phone,
                config={"session_name": session_name or session_id, "db_path": db_path},
            )
            self._clients[session_id] = instance
            return instance

    def connect(self, session_id: str) -> threading.Thread:
        instance = self.get_instance(session_id)
        if not instance:
            raise ValueError(f"Session {session_id} not found")

        def _connect():
            self._set_status(session_id, "connecting")
            if instance.pairing_enabled and instance.pairing_phone:
                self._start_pairing(instance)
            else:
                self._save_qr(session_id, "SCAN_QR_TERMINAL")
            try:
                instance.client.connect()
            except Exception as e:
                console.print(f"[red]Session {session_id} error: {e}[/red]")
                self._set_status(session_id, "error")

        thread = threading.Thread(target=_connect, daemon=True, name=f"wa-{session_id}")
        thread.start()
        instance.thread = thread
        return thread

    def disconnect(self, session_id: str):
        instance = self.get_instance(session_id)
        if instance:
            try:
                instance.client.disconnect()
            except Exception:
                pass
            self._set_status(session_id, "disconnected")

    def remove(self, session_id: str):
        self.disconnect(session_id)
        with self._lock:
            self._clients.pop(session_id, None)

    def send_message(self, session_id: str, jid, text: str) -> bool:
        client = self.get_client(session_id)
        if not client:
            return False
        try:
            from .connection import send_text
            send_text(client, jid, text)
            return True
        except Exception as e:
            console.print(f"[red]Send failed {session_id}: {e}[/red]")
            return False

    def list_sessions(self) -> list[dict]:
        sessions = []
        with self._lock:
            for sid, inst in self._clients.items():
                sessions.append({
                    "session_id": sid, "phone_number": inst.phone_number,
                    "status": inst.status, "pairing_enabled": inst.pairing_enabled,
                })
        return sessions

    def _set_status(self, session_id: str, status: str):
        instance = self.get_instance(session_id)
        if instance:
            instance.status = status
        for cb in self._status_callbacks:
            try:
                cb(session_id, status)
            except Exception:
                pass

    def _start_pairing(self, instance: ClientInstance):
        def _pair():
            time.sleep(3)
            try:
                for method in ['get_pairing_code', 'pairing_code', 'getPairingCode']:
                    if hasattr(instance.client, method):
                        code = getattr(instance.client, method)(instance.pairing_phone)
                        if code:
                            self._save_qr(instance.session_id, str(code))
                            return
                self._save_qr(instance.session_id, "SCAN_QR_TERMINAL")
            except Exception as e:
                self._save_qr(instance.session_id, f"ERROR: {e}")

        threading.Thread(target=_pair, daemon=True).start()

    def _save_qr(self, session_id: str, qr_string: str):
        try:
            server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if server_dir not in sys.path:
                sys.path.insert(0, server_dir)
            from services.session_service import session_service
            session_service.update_qr(session_id, qr_string)
        except Exception as e:
            console.print(f"[red]Failed to save QR: {e}[/red]")

    def _handle_message(self, client: NewClient, msg, session_id: str):
        for callback in self._message_callbacks:
            try:
                callback(client, msg, session_id)
            except Exception as e:
                console.print(f"[red]Message callback error: {e}[/red]")

    def _on_connected(self, session_id: str):
        self._set_status(session_id, "connected")

    def _on_pair(self, session_id: str, ev):
        self._set_status(session_id, "connected")


client_manager = ClientManager()