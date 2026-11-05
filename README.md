# DocCraft

Office document workstation and headless automation engine.

## Verbs
- `doccraft convert --in <file> --out <format>`: Convert office documents (docx, odt, html, md, xlsx, pptx, pdf)
- `doccraft text --in <file>`: Extract readable text and word counts
- `doccraft info --in <file>`: Extract document metadata, page count, and format family
- `doccraft combine <files...> --out <merged.pdf>`: Merge multiple PDF documents
- `doccraft mcp`: FastMCP stdio server

## Status — does today / next week / non-goals

**Does today:** Python FastMCP workstation; 5 test fns; convert/text/combine
family; office-in/PDF-out boundary explicit.

**Next week:** LibreOffice version + headless flags pinned in writing; 3
fixture recipes with measures; manuscript→PDF boundary vs writercraft.

**Non-goals:** PDF ops belong to the pdf side; no cloud conversion.

## Lineage — the Storytold craft-app pattern

Storytold ArtCraft ([storytold/artcraft](https://github.com/storytold/artcraft) — "the IDE for artists") was the starting point. The 16 craft apps in the Storytold stable each ship one binary that is both the human CLI and the agent MCP server (stdio), headless-first, with `run.json` + report artifacts. That modus operandi and harness is what this repo implements; the code here is independent, the pattern is shared.
