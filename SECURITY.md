# Security

Please report vulnerabilities privately through GitHub's "Report a vulnerability" (Security tab) rather than a public issue.

Design notes:
- The wiki must never contain secret values. `wiki check` and `submit_note` reject common key and token formats;
  add your own formats with `secret_patterns` in `agent-wiki.json`. Pattern matching is a safety net, not a guarantee.
- HTTP mode binds to 127.0.0.1 by default. Expose it only through HTTPS (for example a tunnel) and set
  `AGENT_WIKI_HOSTS` to your public host name to enable DNS-rebinding protection for it.
- Tokens are stored as SHA-256 hashes in `$AGENT_WIKI_STATE` (file mode 600) and are masked in the access log.
- `sql` is restricted to read-only statements by a statement check and an SQLite authorizer, on a read-only connection.
