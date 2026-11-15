# agent-wiki

**人和 AI agent 一起维护的多语言知识库。**
以 Markdown + Git 为准，SQLite 全文搜索支持任何语言，自带密钥扫描、每周体检，还有 MCP 服务器，
让 Claude、ChatGPT、Gemini、Codex 能读知识库、提交修改建议。

[English](README.md) · 简体中文 · [日本語](README.ja.md) · [Español](README.es.md)

## 适合谁

- 你经常用 AI agent 干活，但它们换个会话就忘了之前的决定、修过的坑、“这个试过不行”；
- 团队用不止一种语言写东西（比如中英混用），想要一个都能搜到的地方；
- 想让 agent 自己记笔记，但要有人审核，而且不能把密钥写进去。

不适合：要搜几千份原始 PDF / 邮件（用 RAG 工具），或者想要带界面的笔记软件（用 Obsidian，agent-wiki 的文件夹可以直接用 Obsidian 打开）。

## 让 agent 用起来

`wiki init` 会自动生成 `AGENTS.md` 和 `CLAUDE.md`，告诉 Claude Code、Codex、Cursor 等 agent：开工前先 `wiki search`，
做完更新项目页、记一条经验、用 `[[id]]` 互链，最后跑 `wiki check`。在知识库目录里打开 agent 就能直接用，不用额外配置。
一个知识库给多个代码仓库共用时，在每个仓库的 AGENTS.md / CLAUDE.md 里加一句：

```markdown
团队知识在 ~/team-wiki（见其中的 AGENTS.md）。开工前运行 `wiki --root ~/team-wiki search <关键词>`，做完把结果和经验记回去。
```

## 为什么做

Karpathy 提出的 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：不是把原始文档切碎了等提问时再检索（RAG），
而是让 agent **在干活时就写好提炼过、互相链接的条目**，并持续修订。知识会越积越多、越用越好。

| | RAG | LLM Wiki（agent-wiki） |
|---|---|---|
| 存什么 | 原始文档切成碎片 | 提炼后的条目：项目、经验、操作手册 |
| 什么时候加工 | 提问时 | 写入时，之后持续修订 |
| 检索 | 向量相似度 | 全文索引 + `[[链接]]` + 反向链接 |
| 会不会越用越好 | 不会 | 会 |

## 和其他 LLM Wiki 项目的区别

- **任何语言都能搜，不用配置。** 两套 SQLite FTS5 索引并用：词索引（忽略大小写和重音、前缀匹配，适合英、西、法、德等）
  和三字索引（适合中文、日文、韩文、泰文这类不用空格分词的文字）。两个汉字的短词自动退回到规范化子串匹配。
- **六种界面语言。** 提示信息、体检报告和条目模板支持 English、中文、日本語、Español、Français、Deutsch。
  每篇条目也可以用 `lang:` 标注自己的语言。
- **零依赖。** 核心只用 Python 标准库；MCP 是可选扩展。
- **给 agent 的安全护栏。** `wiki check` 拦截 API 密钥、令牌、私钥；agent 通过 MCP 提交的内容只进 **收件箱**，由维护者审核，
  不会直接改知识库；HTTP 访问按客户端发令牌，分 read / write 两种权限，只存哈希。
- **每周体检。** `wiki lint` 找孤立条目、过时条目、标题相近的疑似重复、没有链接的经验，以及写着“已过时 / deprecated / veraltet”的行。
- **网络盘也能用。** 索引先在临时目录建好再复制过去，只读方式打开，适合网络盘、FUSE、同步文件夹。

## 快速上手

```bash
pip install "git+https://github.com/SWYZLCO/agent-wiki"
wiki init my-wiki --lang zh
cd my-wiki
wiki add lesson "部署前先确认 DNS 归属" --slug check-dns --project website --tags dns,deploy
wiki add project "公司官网" --id website
wiki check
wiki search 部署
```

试试自带的示例（一家虚构工作室，条目用了六种语言）：`wiki --root examples/demo-wiki search 迁移`

## 接入 agent（MCP）

```bash
pip install "agent-wiki[mcp] @ git+https://github.com/SWYZLCO/agent-wiki"
claude mcp add wiki -- wiki --root /path/to/my-wiki mcp stdio      # 本机 agent，读写都有
wiki mcp token add chatgpt read                                      # 远程客户端，每个一个令牌
AGENT_WIKI_HOSTS=wiki.example.com wiki mcp http --port 8790
```

放到 HTTPS 后面（例如 Cloudflare Tunnel），网页版连接器用 `https://wiki.example.com/k/<令牌>/mcp`。
工具：`search`、`fetch`、`list_docs`、`stats`、`sql`（只读），write 令牌另有 `submit_note`（投稿进 `inbox/agents/` 等审核）。

命令、配置文件和推荐流程的完整说明见 [英文 README](README.md)。

## 关于 SWYZL & Co.

agent-wiki 来自 [SWYZL & Co.](https://swyzl.tech)（Swyzle Technologies Inc.）的日常工作。我们是一家 AI 驱动的数字化解决方案公司，
位于加拿大大多伦多地区，帮企业设计、搭建和集成业务所依赖的数字系统，并把 AI 用进去：官网与品牌、定制软件、AI 与自动化、集成与长期维护。
Design it. Build it. Add AI.

我们自己的 agent 每天都在这套知识库上工作，跨多个客户和内部项目，中英双语。想在自己公司里用上同样的 AI 工作流，欢迎联系 info@swyzl.tech。

## 许可证

MIT © SWYZL & Co.
