---
paths:
  - ".claude/README.md"
  - ".claude/USAGE.zh-TW.md"
  - ".claude/agent-memory/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/commands/**/*.md"
  - ".claude/hooks/**/*.md"
  - ".claude/rules/**/*.md"
  - ".claude/skills/agent-browser/**/*.md"
  - ".claude/skills/time-skill/**/*.md"
  - ".claude/skills/weather-fetcher/**/*.md"
  - ".claude/skills/weather-svg-creator/**/*.md"
---

# Markdown Docs

> **Scope note (local adaptation):** upstream applies this rule to `**/*.md`. Here `paths` is
> narrowed to an explicit allow-list of the files this install actually ships, so markdown
> this repository owns — including any of its own skills living under `.claude/skills/`
> alongside this install — is not pulled in and governed by the upstream repo's doc layout.
> A broad pattern such as `.claude/**/*.md` would do exactly that. Adding a new asset to this
> install means adding a matching `paths` entry here. The directory conventions below (`best-practice/`,
> `implementation/`, `reports/`, `tips/`) describe the upstream
> [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)
> repo, not this one.

## Documentation Standards

- Keep files focused and concise — one topic per file
- Use relative links between docs (e.g., `../best-practice/claude-memory.md`), not absolute GitHub URLs
- Include back-navigation link at top of best-practice and report docs (see existing files for pattern)
- When adding a new concept or report, update the corresponding table in README.md (CONCEPTS or REPORTS)

## Structure Conventions

- Best practice docs go in `best-practice/`
- Implementation docs go in `implementation/`
- Reports go in `reports/`
- Tips go in `tips/`
- Changelog tracking goes in `changelog/<category>/`

## Formatting

- Use tables for structured comparisons (see README CONCEPTS table as reference)
- Use badge images from `!/tags/` for visual consistency when linking best-practice or implementation docs
- Keep headings hierarchical — don't skip levels (e.g., don't jump from `##` to `####`)
