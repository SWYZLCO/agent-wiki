# agent-wiki

**Una base de conocimiento multilingüe que mantienen juntos las personas y los agentes de IA.**
Markdown + Git como fuente de verdad, búsqueda de texto completo en SQLite para cualquier idioma, detección de
secretos, un chequeo semanal y un servidor MCP para que Claude, ChatGPT, Gemini o Codex la lean y propongan cambios.

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · Español

## ¿Es para ti?

- Trabajas con agentes de IA en muchas sesiones y olvidan decisiones, arreglos y «eso ya lo probamos»;
- tu equipo escribe en más de un idioma y quiere un solo lugar donde buscar;
- quieres que los agentes documenten lo aprendido, con revisión y sin filtrar claves de API.

## Úsala con tu agente

`wiki init` crea `AGENTS.md` y `CLAUDE.md`, que indican a Claude Code, Codex, Cursor y otros: buscar con `wiki search`
antes de empezar, actualizar la página del proyecto y añadir una lección al terminar, enlazar con `[[id]]` y ejecutar `wiki check`.
Abre tu agente en la carpeta de la wiki y listo.

## Qué la hace distinta

- **Búsqueda en cualquier idioma, sin configurar.** Un índice de palabras (sin distinguir mayúsculas ni acentos,
  con prefijos: «precio» encuentra «precios») y un índice de trigramas para escrituras sin espacios (chino, japonés,
  coreano, tailandés) funcionan a la vez.
- **Seis idiomas de interfaz.** Mensajes, informes y plantillas en English, 中文, 日本語, Español, Français y Deutsch.
  Cada página puede indicar su propio `lang:`.
- **Sin dependencias.** El núcleo usa solo la biblioteca estándar de Python; MCP es opcional.
- **Protecciones para agentes.** `wiki check` bloquea claves de API y claves privadas; las notas que envían los agentes
  por MCP van a una **bandeja de entrada** que alguien revisa; el acceso HTTP usa tokens por cliente con rol `read` o `write`.
- **Chequeo semanal.** `wiki lint` lista páginas huérfanas, desactualizadas, títulos casi duplicados y líneas marcadas como obsoletas.

## Empezar

```bash
pip install "git+https://github.com/SWYZLCO/agent-wiki"
wiki init mi-wiki --lang es
cd mi-wiki
wiki add lesson "Comprobar el dueño del DNS antes de desplegar" --project website
wiki check
wiki search desplegar
```

Demo: `wiki --root examples/demo-wiki search precio`

## Conectar agentes (MCP)

```bash
pip install "agent-wiki[mcp] @ git+https://github.com/SWYZLCO/agent-wiki"
claude mcp add wiki -- wiki --root /ruta/a/mi-wiki mcp stdio
wiki mcp token add chatgpt read
AGENT_WIKI_HOSTS=wiki.ejemplo.com wiki mcp http --port 8790
```

Todos los comandos y opciones están en el [README en inglés](README.md).

## Sobre SWYZL & Co.

agent-wiki nace del trabajo diario en [SWYZL & Co.](https://swyzl.tech) (Swyzle Technologies Inc.), un estudio digital
nativo en IA del área metropolitana de Toronto, Canadá. Diseñamos, construimos e integramos los sistemas digitales con los que
funciona un negocio, y ponemos la IA a trabajar dentro de ellos. *Design it. Build it. Add AI.* Contacto: info@swyzl.tech

## Licencia

MIT © SWYZL & Co.
