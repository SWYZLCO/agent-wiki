"""MCP server so agents (Claude, ChatGPT, Gemini, Codex, ...) can read the wiki and submit notes.

- Read tools: search, fetch (the shape ChatGPT connectors expect), list_docs, stats, sql (read-only).
- Write tool: submit_note. Notes never touch the wiki directly; they land in the inbox for review.
- stdio mode (local agents) exposes everything. HTTP mode needs a token per client, with a role
  `read` or `write`. Tokens are stored hashed in $AGENT_WIKI_STATE (default ~/.local/share/agent-wiki).
  Clients send `Authorization: Bearer <token>`, or use the URL form /k/<token>/mcp for web clients
  that cannot set headers. Tokens never appear in the access log.

Needs the optional extra:  pip install "agent-wiki[mcp]"
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import sys
import threading
from pathlib import Path

from . import core
from .i18n import t

MAX_NOTE = 60_000
NOTE_KINDS = ("lesson", "playbook", "project", "correction", "other")
_lock = threading.Lock()
CURRENT_CLIENT: dict = {"name": "local"}


def state_dir(w: core.Wiki) -> Path:
    base = Path(os.environ.get("AGENT_WIKI_STATE", Path.home() / ".local/share/agent-wiki"))
    return base / hashlib.sha1(str(w.root).encode()).hexdigest()[:12]


def log(w: core.Wiki, line: str) -> None:
    f = state_dir(w) / "access.log"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(dt.datetime.now().isoformat(timespec="seconds") + " " + line + "\n")


def instructions(w: core.Wiki) -> str:
    return (f"Knowledge base \"{w.cfg['name']}\": distilled project pages, lessons learned, playbooks and decisions, "
            "maintained by people and agents (LLM-wiki style: written and linked at write time, not raw chunks). "
            "Content may be in several languages; search works across scripts, so try the user's language and "
            "English. Use search first, then fetch(id) for full text. Use sql (read-only SQLite; tables docs, links, "
            "meta) for structured questions. The wiki never stores secret values. If you have write access, use "
            "submit_note for new lessons or corrections; notes are reviewed before they are merged.")


# ---------- tool implementations (plain functions, testable without the MCP SDK) ----------
def t_search(w, query: str, type: str = "", project: str = "", limit: int = 10) -> str:
    with _lock:
        res = core.search(w, query.split(), type, project, "", max(1, min(int(limit), 50)))
    return json.dumps({"results": [{"id": r["id"], "title": r["title"], "url": "wiki://" + r["path"],
                                    "type": r["type"], "lang": r["lang"], "snippet": r["snippet"]} for r in res]},
                      ensure_ascii=False)


def t_fetch(w, id: str) -> str:
    with _lock:
        d = core.get_doc(w, id)
    if not d:
        return json.dumps({"error": t("not_found")}, ensure_ascii=False)
    return json.dumps({"id": d["id"], "title": d["title"], "text": d["body"], "url": "wiki://" + d["path"],
                       "metadata": {k: d[k] for k in ("type", "status", "project", "tags", "related", "updated",
                                                     "lang", "backlinks")}}, ensure_ascii=False)


def t_list_docs(w, type: str = "", project: str = "") -> str:
    with _lock:
        return json.dumps(core.list_docs(w, type, project), ensure_ascii=False)


def t_stats(w) -> str:
    with _lock:
        return json.dumps(core.stats(w), ensure_ascii=False)


def t_sql(w, query: str) -> str:
    try:
        with _lock:
            cols, rows = core.run_sql(w, query)
    except core.WikiError:
        return t("sql_readonly")
    except Exception as e:  # noqa: BLE001
        return f"SQL error: {e}"
    return json.dumps({"columns": cols, "rows": rows}, ensure_ascii=False, default=str)


def t_submit_note(w, title: str, content: str, kind: str = "lesson", project: str = "", update_path: str = "",
                  agent: str = "") -> str:
    kind = kind if kind in NOTE_KINDS else "other"
    if not title.strip() or not content.strip():
        return t("note_empty")
    if len(content) > MAX_NOTE:
        return t("note_long", n=MAX_NOTE)
    hits = core.find_secrets(w, title + "\n" + content)
    if hits:
        return t("note_secret", label=hits[0][0])
    if update_path:
        p = (w.root / update_path).resolve()
        if update_path.startswith("/") or ".." in Path(update_path).parts or w.root not in p.parents:
            return t("note_path")
    now = dt.datetime.now()
    slug = core.slugify(title) or hashlib.sha1(title.encode()).hexdigest()[:8]
    proj = core.slugify(project) or "general"
    box = w.inbox / "agents"
    box.mkdir(parents=True, exist_ok=True)
    f = box / f"{now:%Y-%m-%d-%H%M%S}-{proj}-{slug[:40]}.md"
    who = (agent or CURRENT_CLIENT.get("name", "?")).replace("\n", " ")[:60]
    fm = ["---", f"title: {title.strip()}", f"kind: {kind}", f"project: {proj}", f"submitted_by: {who}",
          f"submitted_at: {now.isoformat(timespec='seconds')}", "status: pending"]
    if update_path:
        fm.append(f"update_path: {update_path}")
    f.write_text("\n".join(fm) + "\n---\n\n" + content.strip() + "\n", encoding="utf-8")
    log(w, f"submit {who} {f.name}")
    return t("note_ok", path=w.rel(f))


# ---------- MCP assembly (works with mcp SDK 1.x FastMCP and 2.x MCPServer) ----------
def _sdk():
    from mcp.types import ToolAnnotations
    try:
        from mcp.server.mcpserver import MCPServer as Server  # mcp >= 2
        return Server, ToolAnnotations, 2
    except ImportError:
        from mcp.server.fastmcp import FastMCP as Server  # mcp 1.x
        return Server, ToolAnnotations, 1


def make_server(w: core.Wiki, write: bool):
    Server, ToolAnnotations, major = _sdk()
    m = Server("agent-wiki", instructions=instructions(w), log_level="WARNING")
    ro = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    @m.tool(annotations=ro, description="Search the wiki (full text, any language; accents and case ignored). "
            "Use a few short keywords. Optional filters: type (e.g. project|lesson|playbook|company), project id. "
            "Returns JSON results with id/title/url/snippet; then call fetch(id).")
    def search(query: str, type: str = "", project: str = "", limit: int = 10) -> str:
        return t_search(w, query, type, project, limit)

    @m.tool(annotations=ro, description="Fetch the full text and metadata of one wiki item by id (e.g. L-0012).")
    def fetch(id: str) -> str:
        return t_fetch(w, id)

    @m.tool(annotations=ro, description="List wiki items, optionally filtered by type and project id.")
    def list_docs(type: str = "", project: str = "") -> str:
        return t_list_docs(w, type, project)

    @m.tool(annotations=ro, description="Overview: counts by type, language and project, and recent updates.")
    def stats() -> str:
        return t_stats(w)

    @m.tool(annotations=ro, description="Run a read-only SQL query (SELECT/WITH) on the index. Tables: "
            "docs(id,type,title,status,project,tags,related,updated,lang,path,body), links(src,dst,rel), meta.")
    def sql(query: str) -> str:
        return t_sql(w, query)

    if write:
        @m.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False,
                                            openWorldHint=False),
                description="Submit a new lesson/playbook/project note, or a correction to an existing file "
                "(set update_path, relative to the wiki root). It goes to the review inbox and is not applied "
                "directly. kind: lesson|playbook|project|correction|other. Never include secret values.")
        def submit_note(title: str, content: str, kind: str = "lesson", project: str = "", update_path: str = "",
                        agent: str = "") -> str:
            return t_submit_note(w, title, content, kind, project, update_path, agent)

    return m, major


def http_app(m, major: int, hosts: list[str]):
    from mcp.server.transport_security import TransportSecuritySettings
    sec = TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=[])
    if major >= 2:
        return m.streamable_http_app(json_response=True, stateless_http=True, transport_security=sec)
    m.settings.json_response = True
    m.settings.stateless_http = True
    m.settings.transport_security = sec
    return m.streamable_http_app()


# ---------- tokens ----------
def tokens_file(w) -> Path:
    return state_dir(w) / "tokens.json"


def load_tokens(w) -> dict:
    f = tokens_file(w)
    return json.loads(f.read_text()) if f.exists() else {}


def save_tokens(w, d: dict) -> None:
    f = tokens_file(w)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    os.chmod(f, 0o600)


def _hash(tok: str) -> str:
    return hashlib.sha256(tok.encode()).hexdigest()


def cmd_token(w, args: list[str]) -> None:
    d = load_tokens(w)
    if args[:1] == ["add"] and len(args) == 3 and args[2] in ("read", "write"):
        tok = "wk_" + secrets.token_urlsafe(32)
        d[_hash(tok)] = {"name": args[1], "role": args[2], "created": dt.date.today().isoformat()}
        save_tokens(w, d)
        print(tok)
    elif args[:1] == ["list"]:
        for h, v in d.items():
            print(f"{v['name']} · {v['role']} · {v['created']} · {h[:10]}")
    elif args[:1] == ["revoke"] and len(args) == 2:
        n = len(d)
        d = {h: v for h, v in d.items() if v["name"] != args[1]}
        save_tokens(w, d)
        print(f"revoked {n - len(d)}")
    else:
        sys.exit("Usage: wiki mcp token add NAME read|write | token list | token revoke NAME")


def authorize(w, path: str, headers: dict) -> tuple[dict | None, str]:
    """Return (token info or None, path with any /k/<token> prefix removed)."""
    tok = ""
    m = re.match(r"^/k/([A-Za-z0-9_\-]+)(/mcp/?)$", path)
    if m:
        tok, path = m.group(1), m.group(2)
    else:
        v = headers.get(b"authorization", b"")
        if v:
            tok = (v[7:] if v.lower().startswith(b"bearer ") else v).decode().strip()
    return (load_tokens(w).get(_hash(tok)) if tok else None), path


# ---------- HTTP ----------
def run_http(w: core.Wiki, port: int, host: str = "127.0.0.1") -> None:
    import uvicorn

    hosts = ["127.0.0.1:*", "localhost:*"] + [h.strip() for h in os.environ.get("AGENT_WIKI_HOSTS", "").split(",")
                                              if h.strip()]
    apps = {}
    for role, write in (("read", False), ("write", True)):
        srv, major = make_server(w, write)
        apps[role] = http_app(srv, major, hosts)

    async def send_json(send, status, obj):
        body = json.dumps(obj).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            async with contextlib.AsyncExitStack() as stack:
                for a in apps.values():
                    await stack.enter_async_context(a.router.lifespan_context(a))
                while True:
                    msg = await receive()
                    if msg["type"] == "lifespan.startup":
                        await send({"type": "lifespan.startup.complete"})
                    elif msg["type"] == "lifespan.shutdown":
                        await send({"type": "lifespan.shutdown.complete"})
                        return
        if scope["type"] != "http":
            return
        path = scope["path"]
        if path == "/healthz":
            return await send_json(send, 200, {"ok": True})
        headers = dict(scope.get("headers", []))
        shown = re.sub(r"^/k/[^/]+", "/k/***", path)
        ip = headers.get(b"cf-connecting-ip", b"").decode() or (scope.get("client") or ["?"])[0]
        if "/.well-known/" in path:
            return await send_json(send, 404, {"error": "no oauth; use a token"})
        info, path = authorize(w, path, headers)
        if not info:
            log(w, f"deny {ip} {scope['method']} {shown}")
            return await send_json(send, 401, {"error": "unauthorized"})
        if path.rstrip("/") != "/mcp":
            return await send_json(send, 404, {"error": "not found"})
        CURRENT_CLIENT["name"] = info["name"]
        log(w, f"ok {info['name']} {info['role']} {ip} {scope['method']}")
        scope = dict(scope, path="/mcp", raw_path=b"/mcp")
        await apps[info["role"]](scope, receive, send)

    uvicorn.run(app, host=host, port=port, log_level="warning", proxy_headers=True)


def main(w: core.Wiki, pos: list[str], opts: dict) -> None:
    if not pos or pos[0] in ("-h", "--help"):
        print(__doc__)
    elif pos[0] == "stdio":
        srv, _ = make_server(w, True)
        srv.run("stdio")
    elif pos[0] == "http":
        run_http(w, int(opts.get("port", os.environ.get("AGENT_WIKI_PORT", 8790))), opts.get("host", "127.0.0.1"))
    elif pos[0] == "token":
        cmd_token(w, pos[1:])
    else:
        print(__doc__)
        sys.exit(2)
