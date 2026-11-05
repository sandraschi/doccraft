# DocCraft

Office document workstation and headless automation engine.

## Verbs
- `doccraft convert --in <file> --out <format>`: Convert office documents (docx, odt, html, md, xlsx, pptx, pdf)
- `doccraft text --in <file>`: Extract readable text and word counts
- `doccraft info --in <file>`: Extract document metadata, page count, and format family
- `doccraft combine <files...> --out <merged.pdf>`: Merge multiple PDF documents
- `doccraft mcp`: FastMCP stdio server

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
