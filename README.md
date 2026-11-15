# agent-wiki

**Give your AI agents a memory that your whole team can read.**
agent-wiki is a small, multilingual knowledge base that people and AI coding agents (Claude Code, Codex,
Cursor, Gemini CLI, ChatGPT) maintain together. Agents look things up before they work and write down what they
learned after. Everything stays as plain Markdown in Git.

English · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Español](README.es.md)

Built and used in production by [SWYZL & Co.](https://swyzl.tech), an AI-native digital studio.

```text
$ wiki search 迁移            # Chinese, 2 characters
[lesson] L-0003 · 会员迁移时先关闭旧系统的自动续费 · zh
$ wiki search deployer        # French "Déployer", accent ignored
[playbook] deploy-website · Déployer le site (Cloudflare Workers) · fr
$ wiki search 予約確認         # Japanese
[lesson] L-0004 · 予約確認メールは送信元ドメインの認証を先に設定する · ja
```

## Is this for you?

Use it if:

- you work with AI agents across many sessions and they keep forgetting decisions, fixes and "we tried that already";
- your team writes in more than one language (for example English and Chinese) and wants one searchable place;
- you want agents to write knowledge down, but with review and without leaking API keys.

Skip it if you need to search thousands of raw PDFs or emails (use a RAG tool for that), or you want a
polished note-taking app with a UI (try Obsidian; agent-wiki folders open fine in it).

## 5-minute walkthrough

**1. Install** (Python 3.9+, no other dependencies; PyPI release coming):

```bash
pip install "git+https://github.com/SWYZLCO/agent-wiki"
```

or clone it (`git clone https://github.com/SWYZLCO/agent-wiki && cd agent-wiki && pip install .`) to try the demo wiki.

**2. Create a wiki** in the language your team writes in (`en`, `zh`, `ja`, `es`, `fr`, `de`):

```bash
wiki init ~/team-wiki --lang en
cd ~/team-wiki
```

```text
team-wiki/
  agent-wiki.json   settings
  AGENTS.md         instructions for your coding agent (Codex, Cursor and others read this)
  CLAUDE.md         the same for Claude Code (imports AGENTS.md)
  company/  projects/  lessons/  playbooks/  inbox/
```

**3. Write your first page** (or let your agent do it):

```bash
wiki add lesson "Check DNS ownership before deploying" --project website --tags dns,deploy
```

```text
Created lessons/L-0001-check-dns-ownership-before-deploying.md (id L-0001). Fill in the body, then run `wiki check`.
```

The file is a template with three headings: *What happened*, *Lesson (what to do next time)*, *Evidence*.

**4. Find it again, in any language:**

```bash
wiki search dns
wiki show L-0001
```

**5. Keep it healthy:**

```bash
wiki check          # missing fields, broken [[links]], secrets -> exits 1 if something is wrong
wiki lint --write   # weekly: orphans, stale pages, duplicates, contradictions -> report in inbox/
```

Want to see a filled-in wiki first? `wiki --root examples/demo-wiki stats` shows a fictional studio with pages in
six languages.

## Use it with your agent

**Option A, zero setup (recommended to start).** Open your agent in the wiki folder, or add the wiki path to
your project's agent instructions. `wiki init` already wrote `AGENTS.md` / `CLAUDE.md`, which tell the agent to:
search before starting, update the project page and add a lesson after finishing, link pages with `[[id]]`, and run
`wiki check`. The agent uses the `wiki` command like any other shell tool.

To use one wiki from many code repositories, add this to each repository's `AGENTS.md` or `CLAUDE.md`:

```markdown
Team knowledge lives in ~/team-wiki (see its AGENTS.md). Run `wiki --root ~/team-wiki search <keywords>`
before starting, and record results and lessons there when you finish.
```

**Option B, MCP tools** (for agents without a shell, or remote clients):

```bash
pip install "agent-wiki[mcp] @ git+https://github.com/SWYZLCO/agent-wiki"
claude mcp add wiki -- wiki --root ~/team-wiki mcp stdio      # Claude Code; similar for Codex / Gemini CLI
```

For claude.ai or ChatGPT custom connectors, run it over HTTP with one token per client:

```bash
wiki mcp token add chatgpt read          # prints the token once; only a hash is stored
wiki mcp token add claude-web write
AGENT_WIKI_HOSTS=wiki.example.com wiki mcp http --port 8790
```

Put it behind HTTPS (for example a Cloudflare Tunnel). Connector URL: `https://wiki.example.com/k/<token>/mcp`,
or send `Authorization: Bearer <token>`. Tools: `search`, `fetch`, `list_docs`, `stats`, `sql` (read-only), and for
write tokens `submit_note`, which puts a note in `inbox/agents/` for a person or agent to review. It never edits
pages directly.

## Why a wiki and not RAG

Andrej Karpathy described the [LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):
instead of chunking raw documents and searching them at question time (RAG), an agent **writes distilled, linked
pages as it works** and keeps revising them, so knowledge compounds.

| | RAG | LLM wiki (agent-wiki) |
|---|---|---|
| What is stored | raw documents cut into chunks | distilled pages: projects, lessons, playbooks |
| When it is processed | at question time | at write time, then revised |
| Retrieval | vector similarity | full-text index + `[[links]]` + backlinks |
| Gets better with use | no | yes |
| Best for | large, static corpora | small-to-medium, fast-changing team knowledge |

## How it compares

There are many LLM-wiki projects ([GitHub topic](https://github.com/topics/karpathy-llm-wiki)). Here is where
agent-wiki is different, and where it is not:

| | agent-wiki | typical LLM-wiki project |
|---|---|---|
| Search in Chinese / Japanese / Korean / Thai | yes, built in (trigram index + short-word fallback) | often English-only tokenization or needs embeddings |
| Accent- and case-insensitive (café = cafe) | yes | varies |
| Interface and templates in 6 languages | yes | usually English only |
| Dependencies | none (Python standard library) | often a vector DB, an embedding API or a desktop app |
| Agent writes go through review | yes (MCP inbox) | usually write directly |
| Secret scanning on every check and every agent note | yes | rare |
| Per-client tokens with read/write roles | yes | varies |
| Weekly lint for orphans, stale pages, contradictions | yes | some |
| Works on network drives and synced folders | yes (immutable SQLite, temp-dir builds) | rarely considered |
| Semantic (vector) search | **no**, keyword and substring only | some have it |
| GUI / graph view | **no**, use Obsidian or your editor | some have it |

## Reference

### Page format

```markdown
---
id: L-0003
type: lesson
title: Turn off auto-renew in the old system before migrating members
status: active
project: [booking-app]
tags: [stripe, migration]
updated: 2026-11-08
lang: en
---
```

### Commands

| Command | What it does |
|---|---|
| `wiki init [DIR] --lang L` | create a wiki (with AGENTS.md / CLAUDE.md) |
| `wiki search TERM... [--type] [--project] [--lang] [--json]` | full-text search; all terms must match |
| `wiki list [TYPE]`, `wiki show ID` | browse; `show` also lists backlinks |
| `wiki add lesson\|project\|playbook "Title"` | new page from a template in the wiki's language |
| `wiki check` | required fields, duplicate ids, broken links, secret scan; exit code 1 on problems (CI / pre-commit) |
| `wiki lint [--write]` | health check; `--write` saves the report to `inbox/` |
| `wiki stats`, `wiki sql "SELECT ..."` | overview and read-only SQL |
| `wiki export-sql out.sql` | dump the index, e.g. into Cloudflare D1 for a read-only web view |
| `wiki mcp stdio\|http\|token ...` | MCP server |

Global option `--root DIR` (or `AGENT_WIKI_ROOT`); output language from `AGENT_WIKI_LANG` or the wiki's `language`.

### Settings (`agent-wiki.json`)

```json
{
  "name": "Northwind Studio",
  "language": "en",
  "sections": {"company": "company", "projects": "project", "lessons": "lesson", "playbooks": "playbook"},
  "extra_sources": [{"dir": "../reports", "type": "report", "glob": "*.md", "prefix": "R:"}],
  "stale_days": {"project": 21, "playbook": 60, "company": 60},
  "lesson_prefix": "L-",
  "project_keywords": {"website": "website"},
  "secret_patterns": [["acme_[A-Za-z0-9]{24}", "Acme API key"]]
}
```

`extra_sources` makes other Markdown folders (reports, meeting notes) searchable without treating them as wiki
pages. Put your own `templates/lesson.md` etc. in the wiki to override the built-in templates.

## About SWYZL & Co.

agent-wiki comes out of daily work at [SWYZL & Co.](https://swyzl.tech) (Swyzle Technologies Inc.), an
AI-native digital studio in the Greater Toronto Area, Canada. We design, build and integrate the digital
systems a business runs on, and put AI to work inside them: websites and brand, custom software, AI agents and
automation, integration and long-term care. *Design it. Build it. Add AI.*

Our own agents run on this wiki every day across several client and internal projects, in English and Chinese.
If you want the same kind of AI workflow inside your business, write to info@swyzl.tech.

## Contributing

Bug reports, new interface languages and search improvements are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © SWYZL & Co.
