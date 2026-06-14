"""
server/scripts/admin.py — HDM BOT Admin CLI (Unified)
Run: python server/scripts/admin.py

CLI for managing: Sessions, Commands, Settings, Database, Admin Users.
"""
from __future__ import annotations

import os
import sys
import time
import hashlib
from datetime import datetime

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(os.path.dirname(_current_dir))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(_current_dir), ".env"))

from pymongo import MongoClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box

console = Console()
_mongo: MongoClient | None = None
_db = None

# ===================================================================
# DATABASE
# ===================================================================

def get_db():
    global _mongo, _db
    if _mongo is None:
        try:
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/hdm-bot")
            _mongo = MongoClient(uri)
            db_name = uri.split("/")[-1].split("?")[0] or "hdm_bot"
            _db = _mongo[db_name]
        except Exception as e:
            console.print(f"[red]MongoDB connection failed: {e}[/red]")
            return None
    return _db


def list_collections():
    db = get_db()
    return sorted(db.list_collection_names()) if db is not None else []


def collection_stats(name: str):
    db = get_db()
    if db is None:
        return None
    col = db[name]
    return {"name": name, "documents": col.estimated_document_count(), "indexes": len(col.index_information())}


def drop_collection(name: str) -> bool:
    db = get_db()
    if db is None:
        return False
    try:
        db.drop_collection(name)
        return True
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        return False


def drop_database() -> bool:
    global _mongo, _db
    if _mongo is None:
        return False
    try:
        db_name = _db.name
        _mongo.drop_database(db_name)
        _db = None
        console.print(f"[green]✓ Database '{db_name}' dropped.[/green]")
        return True
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        return False


# ===================================================================
# UI HELPERS
# ===================================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    clear()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", border_style="cyan",
        subtitle=f"[dim]HDM BOT Admin | {datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]"))
    console.print()


def pause():
    console.print("\n[dim]Press Enter to return...[/dim]")
    input()


# ===================================================================
# AUTH HELPERS
# ===================================================================

def hash_password(password: str) -> str:
    salt = os.getenv("JWT_SECRET", "hdm_bot_secret")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


# ===================================================================
# 1. ADMIN USER MANAGEMENT
# ===================================================================

def admin_list():
    print_header("👑 Admin Users")
    db = get_db()
    if db is None:
        return pause()
    users = list(db["users"].find())
    if not users:
        console.print("[yellow]No admin users found.[/yellow]")
        return pause()
    table = Table(box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Email", style="cyan")
    table.add_column("Username", style="green")
    table.add_column("Role", style="yellow")
    table.add_column("Active", style="magenta")
    table.add_column("Last Login", style="dim")
    for i, u in enumerate(users, 1):
        table.add_row(str(i), u.get("email",""), u.get("username",""), u.get("role",""),
            "✓" if u.get("is_active") else "✗", str(u.get("last_login","Never"))[:16])
    console.print(table)
    console.print(f"\n[dim]Total: {len(users)} admin users[/dim]")
    pause()


def admin_create():
    print_header("➕ Create Admin User")
    db = get_db()
    if db is None:
        return pause()
    email = Prompt.ask("Email", default="admin@hdm-bot.com")
    username = Prompt.ask("Username", default="admin")
    password = Prompt.ask("Password", default="admin123", password=True)
    role = Prompt.ask("Role", default="admin", choices=["owner","super_admin","admin","viewer"])
    existing = db["users"].find_one({"$or": [{"email": email}, {"username": username}]})
    if existing is not None:
        console.print(f"[yellow]User already exists: {existing.get('email')}[/yellow]")
        return pause()
    doc = {
        "username": username, "email": email,
        "password_hash": hash_password(password), "role": role,
        "phone_number": os.getenv("OWNER_NUMBER",""),
        "is_active": True,
        "permissions": ["*"] if role in ("owner","super_admin") else ["dashboard.view","commands.manage","autoreplies.manage","messages.view","contacts.manage","broadcasts.manage","settings.view","sessions.view"],
        "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "last_login": None,
    }
    db["users"].insert_one(doc)
    console.print(f"\n[green]✓ Admin created![/green]")
    console.print(f"  Email: {email}\n  Username: {username}\n  Password: {password}\n  Role: {role}")
    pause()


def admin_manage():
    print_header("🔧 Manage Admin User")
    db = get_db()
    if db is None:
        return pause()
    users = list(db["users"].find())
    if not users:
        console.print("[yellow]No users found.[/yellow]")
        return pause()
    for i, u in enumerate(users, 1):
        icon = "🟢" if u.get("is_active") else "🔴"
        console.print(f"  [bold cyan]{i}.[/bold cyan] {icon} {u.get('email')} ({u.get('role')})")
    console.print()
    try:
        idx = IntPrompt.ask("Select user", default=0)
        if idx < 1 or idx > len(users):
            return pause()
        user = users[idx - 1]
        print_header(f"Manage: {user.get('email')}")
        console.print(f"  Username: {user.get('username')}")
        console.print(f"  Role: {user.get('role')}")
        console.print(f"  Active: {user.get('is_active')}")
        console.print()
        console.print("  [bold cyan]1.[/bold cyan] Toggle Active")
        console.print("  [bold cyan]2.[/bold cyan] Change Role")
        console.print("  [bold cyan]3.[/bold cyan] Reset Password")
        console.print()
        action = IntPrompt.ask("Action", default=0)
        if action == 1:
            new_active = not user.get("is_active", True)
            db["users"].update_one({"_id": user["_id"]}, {"$set": {"is_active": new_active}})
            console.print(f"[green]✓ Active: {new_active}[/green]")
        elif action == 2:
            new_role = Prompt.ask("New role", choices=["owner","super_admin","admin","viewer"])
            db["users"].update_one({"_id": user["_id"]}, {"$set": {"role": new_role}})
            console.print(f"[green]✓ Role: {new_role}[/green]")
        elif action == 3:
            new_pass = Prompt.ask("New password", password=True)
            db["users"].update_one({"_id": user["_id"]}, {"$set": {"password_hash": hash_password(new_pass)}})
            console.print(f"[green]✓ Password reset to: {new_pass}[/green]")
    except ValueError:
        pass
    pause()


def admin_delete():
    print_header("🗑️ Delete Admin User")
    db = get_db()
    if db is None:
        return pause()
    users = list(db["users"].find())
    if not users:
        console.print("[yellow]No users found.[/yellow]")
        return pause()
    for i, u in enumerate(users, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] {u.get('email')} ({u.get('role')})")
    console.print()
    try:
        idx = IntPrompt.ask("Select user to delete", default=0)
        if 1 <= idx <= len(users):
            user = users[idx - 1]
            if Confirm.ask(f"[red]Delete {user.get('email')}?[/red]", default=False):
                db["users"].delete_one({"_id": user["_id"]})
                console.print(f"[green]✓ Deleted.[/green]")
    except ValueError:
        pass
    pause()


# ===================================================================
# 2. SESSION MANAGEMENT
# ===================================================================

def sessions_list():
    print_header("📱 WhatsApp Sessions")
    from server.whatsapp.client_manager import client_manager
    sessions = client_manager.list_sessions()
    if not sessions:
        console.print("[yellow]No sessions.[/yellow]")
        return pause()
    table = Table(box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("Phone", style="green")
    table.add_column("Status", style="yellow")
    for s in sessions:
        colors = {"connected":"green","connecting":"yellow","disconnected":"red","error":"red"}
        table.add_row(s["session_id"], s.get("phone_number","N/A"), f"[{colors.get(s['status'],'white')}]{s['status']}[/{colors.get(s['status'],'white')}]")
    console.print(table)
    pause()


def session_create():
    print_header("➕ Create Session")
    from server.whatsapp.client_manager import client_manager
    sid = Prompt.ask("Session ID", default="session_2")
    phone = Prompt.ask("Phone", default="")
    name = Prompt.ask("Name", default=sid)
    pairing = Confirm.ask("Pairing?", default=False)
    try:
        client_manager.create_client(session_id=sid, session_name=name, phone_number=phone, pairing_enabled=pairing, pairing_phone=phone if pairing else "")
        console.print(f"\n[green]✓ Created '{sid}'[/green]")
        if Confirm.ask("Connect?", default=True):
            client_manager.connect(sid)
            console.print("[green]✓ Connecting...[/green]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
    pause()


def session_manage():
    from server.whatsapp.client_manager import client_manager
    sessions = client_manager.active_sessions
    if not sessions:
        console.print("[yellow]No sessions.[/yellow]")
        return pause()
    print_header("🔧 Manage Session")
    for i, sid in enumerate(sessions, 1):
        s = client_manager.get_status(sid)
        icon = {"connected":"🟢","connecting":"🟡","disconnected":"🔴"}.get(s,"⚪")
        console.print(f"  [bold cyan]{i}.[/bold cyan] {icon} {sid} ({s})")
    try:
        idx = IntPrompt.ask("Select", default=1)
        if 1 <= idx <= len(sessions):
            sid = sessions[idx-1]
            print_header(f"Session: {sid}")
            console.print("1. Disconnect\n2. Reconnect\n3. Remove\n")
            a = IntPrompt.ask("Action", default=0)
            if a == 1: client_manager.disconnect(sid); console.print("[green]✓[/green]")
            elif a == 2: client_manager.connect(sid); console.print("[green]✓[/green]")
            elif a == 3 and Confirm.ask("Remove?", default=False): client_manager.remove(sid); console.print("[green]✓[/green]")
    except ValueError: pass
    pause()


def session_delete():
    from server.whatsapp.client_manager import client_manager
    sessions = client_manager.active_sessions
    if not sessions:
        console.print("[yellow]No sessions.[/yellow]")
        return pause()
    print_header("🗑️ Delete Session")
    for i, sid in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] {sid}")
    try:
        idx = IntPrompt.ask("Select", default=0)
        if 1 <= idx <= len(sessions) and Confirm.ask("Delete?", default=False):
            client_manager.remove(sessions[idx-1])
            console.print("[green]✓[/green]")
    except ValueError: pass
    pause()


# ===================================================================
# 3. COMMAND MANAGEMENT
# ===================================================================

def commands_list():
    print_header("📋 Commands")
    from server.whatsapp.connection import _COMMANDS, get_prefix
    table = Table(box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Command", style="cyan")
    for i, n in enumerate(sorted(_COMMANDS.keys()), 1):
        table.add_row(str(i), f"{get_prefix()}{n}")
    console.print(table)
    console.print(f"\n[dim]Total: {len(_COMMANDS)}[/dim]")
    pause()


def commands_add():
    print_header("➕ Add Command")
    from server.whatsapp.connection import _COMMANDS, get_prefix, send_text
    name = Prompt.ask("Command name")
    response = Prompt.ask("Response")
    if name and response:
        def custom(client, jid, args, **kw):
            send_text(client, jid, response)
        _COMMANDS[name.lower()] = custom
        console.print(f"[green]✓ {get_prefix()}{name} added (runtime)[/green]")
    pause()


def commands_remove():
    print_header("➖ Remove Command")
    from server.whatsapp.connection import _COMMANDS
    names = sorted(_COMMANDS.keys())
    for i, n in enumerate(names, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] {n}")
    try:
        idx = IntPrompt.ask("Select", default=0)
        if 1 <= idx <= len(names) and Confirm.ask(f"Remove '{names[idx-1]}'?", default=False):
            del _COMMANDS[names[idx-1]]
            console.print("[green]✓[/green]")
    except ValueError: pass
    pause()


# ===================================================================
# 4. SETTINGS
# ===================================================================

def settings_view():
    print_header("⚙️ Settings")
    from server.whatsapp.connection import get_prefix
    table = Table(box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    for k in ["BOT_NAME","SESSION_NAME","OWNER_NUMBER","ADMIN_NUMBERS","ENABLE_AI_COMMANDS","ENABLE_BUG_COMMANDS","DEFAULT_AI_MODEL","FLASK_HOST","FLASK_PORT","MONGODB_URI"]:
        v = os.getenv(k,"")
        table.add_row(k, v[:60] if v else "-")
    table.add_row("PREFIX", get_prefix())
    console.print(table)
    pause()


def settings_edit():
    print_header("✏️ Edit")
    from server.whatsapp.connection import get_prefix, set_prefix
    console.print("1. Prefix\n2. Owner\n3. Add Admin\n4. Remove Admin\n5. Toggle AI\n6. Toggle Bug\n")
    try:
        c = IntPrompt.ask("Select", default=0)
        if c == 1:
            p = Prompt.ask("New prefix")
            if p: set_prefix(p[:3]); console.print(f"[green]✓ {get_prefix()}[/green]")
        elif c == 2:
            n = Prompt.ask("New owner")
            if n: os.environ["OWNER_NUMBER"] = n; console.print(f"[green]✓[/green]")
        elif c == 3:
            n = Prompt.ask("Number")
            if n:
                cur = os.getenv("ADMIN_NUMBERS","")
                os.environ["ADMIN_NUMBERS"] = f"{cur},{n}" if cur else n
                console.print("[green]✓[/green]")
        elif c == 4:
            n = Prompt.ask("Number")
            if n:
                cur = os.getenv("ADMIN_NUMBERS","")
                os.environ["ADMIN_NUMBERS"] = ",".join([x for x in cur.split(",") if x != n])
                console.print("[green]✓[/green]")
        elif c == 5:
            v = Confirm.ask("Enable AI?", default=True)
            os.environ["ENABLE_AI_COMMANDS"] = str(v).lower()
            console.print(f"[green]✓ {'ON' if v else 'OFF'}[/green]")
        elif c == 6:
            v = Confirm.ask("Enable Bug?", default=True)
            os.environ["ENABLE_BUG_COMMANDS"] = str(v).lower()
            console.print(f"[green]✓ {'ON' if v else 'OFF'}[/green]")
    except ValueError: pass
    pause()


# ===================================================================
# 5. DATABASE
# ===================================================================

def db_list():
    print_header("🗄️ Collections")
    cols = list_collections()
    if not cols:
        console.print("[yellow]None[/yellow]")
    else:
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Collection", style="cyan")
        table.add_column("Docs", style="green")
        for i, n in enumerate(cols, 1):
            s = collection_stats(n)
            table.add_row(str(i), n, str(s["documents"]) if s is not None else "?")
        console.print(table)
    pause()


def db_drop_col():
    print_header("🗑️ Drop Collection")
    cols = list_collections()
    if not cols:
        console.print("[yellow]None[/yellow]")
    for i, n in enumerate(cols, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] {n}")
    try:
        idx = IntPrompt.ask("Select", default=0)
        if 1 <= idx <= len(cols) and Confirm.ask(f"[red]DROP '{cols[idx-1]}'?[/red]", default=False):
            if drop_collection(cols[idx-1]): console.print("[green]✓[/green]")
    except ValueError: pass
    pause()


def db_drop_all():
    print_header("💀 Drop Database")
    console.print(Panel("[bold red]⚠️ This deletes ALL data![/bold red]", border_style="red"))
    if Confirm.ask("[red]Are you sure?[/red]", default=False):
        db_name = os.getenv("MONGODB_URI","").split("/")[-1].split("?")[0] or "hdm_bot"
        if Confirm.ask(f"[red]Type '{db_name}' to confirm:[/red]", default=""):
            if drop_database(): console.print("[green]✓[/green]")
    pause()


# ===================================================================
# MAIN
# ===================================================================

def main_menu():
    while True:
        print_header("🚀 HDM BOT Admin")
        from server.whatsapp.client_manager import client_manager
        sessions = client_manager.list_sessions()
        connected = sum(1 for s in sessions if s["status"] == "connected")
        from server.whatsapp.connection import _COMMANDS
        console.print(f"  [dim]Sessions: {len(sessions)} ({connected} connected) | Commands: {len(_COMMANDS)}[/dim]")
        console.print()
        console.print("  [bold cyan]1.[/bold cyan] 👑 Admin Users (List/Create/Manage/Delete)")
        console.print("  [bold cyan]2.[/bold cyan] 📱 Sessions (List/Create/Manage/Delete)")
        console.print("  [bold cyan]3.[/bold cyan] 📋 Commands (List/Add/Remove)")
        console.print("  [bold cyan]4.[/bold cyan] ⚙️ Settings (View/Edit)")
        console.print("  [bold cyan]5.[/bold cyan] 🗄️ Database (List/Drop Collection/Drop DB)")
        console.print("  [bold cyan]0.[/bold cyan] 🚪 Exit")
        console.print()
        try:
            c = IntPrompt.ask("Select", default=0)
            if c == 1: _submenu("👑 Admin Users", {"List": admin_list, "Create": admin_create, "Manage": admin_manage, "Delete": admin_delete})
            elif c == 2: _submenu("📱 Sessions", {"List": sessions_list, "Create": session_create, "Manage": session_manage, "Delete": session_delete})
            elif c == 3: _submenu("📋 Commands", {"List": commands_list, "Add": commands_add, "Remove": commands_remove})
            elif c == 4: _submenu("⚙️ Settings", {"View": settings_view, "Edit": settings_edit})
            elif c == 5: _submenu("🗄️ Database", {"List Collections": db_list, "Drop Collection": db_drop_col, "Drop Database": db_drop_all})
            elif c == 0: console.print("\n[yellow]Goodbye![/yellow]"); break
        except ValueError: pass


def _submenu(title: str, options: dict):
    while True:
        print_header(title)
        for i, (label, _) in enumerate(options.items(), 1):
            console.print(f"  [bold cyan]{i}.[/bold cyan] {label}")
        console.print("  [bold cyan]0.[/bold cyan] [dim]Back[/dim]\n")
        try:
            c = IntPrompt.ask("Select", default=0)
            if c == 0: return
            for i, (_, fn) in enumerate(options.items(), 1):
                if i == c: fn(); break
        except ValueError: pass


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "--list": admin_list()
            elif sys.argv[1] == "--create": admin_create()
            else: main_menu()
        else:
            main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        import traceback; traceback.print_exc()
        input("\nPress Enter...")