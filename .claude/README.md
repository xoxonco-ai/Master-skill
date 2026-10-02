# Claude Code setup — installed from `claude-code-best-practice`

This directory is an install of [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice).

> 📘 **繁體中文操作手冊：[`USAGE.zh-TW.md`](USAGE.zh-TW.md)** — 名詞中文對照、完整指令表、
> 每個設定在做什麼、以及照抄這套架構寫自己工作流的三步驟範本。

| | |
|---|---|
| Upstream | `https://github.com/shanraisshan/claude-code-best-practice.git` |
| Commit | `20d8f78bdc18f7a637bbb3f3902f1c1e3a3b8563` (2026-08-24) |
| Scope | `.claude/` tree + root `.mcp.json`, trimmed to what applies to this repo |
| License | MIT (upstream) |

## What's here

| Path | What it is |
|---|---|
| `settings.json` | Permissions, hooks wiring, status line, output style, `plansDirectory`, env |
| `hooks/` | Cross-platform sound-notification system (`scripts/hooks.py`, 30 hook events, `sounds/`) |
| `agents/` | Subagents: `weather-agent`, `time-agent` |
| `commands/` | `/weather-orchestrator`, `/time-command` |
| `skills/` | `weather-fetcher`, `weather-svg-creator`, `time-skill`, `agent-browser` |
| `rules/` | Path-scoped memory rule (`markdown-docs.md`) |
| `agent-memory/` | Upstream demo of the auto-memory feature (`weather-agent`) |
| `../.mcp.json` | Project MCP servers: `playwright`, `context7`, `deepwiki` (via `npx`) |

## Try it

```bash
claude
/weather-orchestrator     # command -> agent -> skill demo; writes orchestration-workflow/
/time-command             # minimal command -> skill demo
```

Hook sounds need an audio player on `PATH`: `afplay` (macOS, built in), or `paplay` /
`aplay` / `ffplay` / `mpg123` (Linux). Without one, `hooks.py` exits 0 silently — hooks never
block a session.

## Local adaptations

Everything is upstream-verbatim except:

1. **`settings.json`** — dropped the upstream author's personal `spinnerVerbs` and
   `spinnerTipsOverride`; replaced the placeholder `statusLine` with a "directory · branch"
   command.

   `extraKnownMarketplaces` and `enabledPlugins` are **not** from
   `claude-code-best-practice`. They were added deliberately afterwards, on request, to match
   the `my-frist-project` copy of this install — `superpowers` first, by its own separate
   change, then the remaining four. Together they auto-enable five third-party skill
   marketplaces on every session in this repository:

   | Marketplace | Source repo | Plugin enabled |
   |---|---|---|
   | `superpowers-marketplace` | `obra/superpowers-marketplace` | `superpowers` |
   | `baoyu-skills` | `JimLiu/baoyu-skills` | `baoyu-skills` |
   | `hyperframes` | `heygen-com/hyperframes` | `hyperframes` |
   | `antv-infographic` | `antvis/Infographic` | `antv-infographic-skills` |
   | `caveman` | `JuliusBrussee/caveman` | `caveman` |

   These are third-party repositories outside this project's control: whatever they ship is
   loaded as skills here, and it changes whenever they push. Remove either key to opt out;
   removing a marketplace from `extraKnownMarketplaces` without removing its entry from
   `enabledPlugins` leaves a plugin pointing at an unknown marketplace, so take both out
   together. The rest of this install works unchanged without them.
2. **`rules/markdown-docs.md`** — `paths` narrowed from `**/*.md` to an explicit allow-list of
   the files this install ships. Not `.claude/**/*.md`: this repository had no `.claude/`
   before this install, but the moment it gains a skill of its own there, that pattern would
   silently start imposing the upstream repo's doc layout on it. The allow-list cannot. Adding
   an asset to this install means adding a matching `paths` entry.
3. **Root `.gitignore`** — unchanged, and deliberately so. This repository does not ignore
   `.claude/`, so the install is tracked as-is; `git check-ignore` was run against
   `settings.json`, `rules/markdown-docs.md` and `.mcp.json` to confirm nothing here is
   silently untracked. (The `my-frist-project` copy of this install *did* need a `.gitignore`
   rewrite, because that repo ignored `.claude/` wholesale.)

4. **Chinese labels** — every `description` is prefixed with a bracketed Chinese label so the
   `/` menu and skill picker are scannable. `name` fields are untouched: the spec requires
   lowercase ASCII matching the directory name, so only `description` is safe to localise.
5. **21 upstream-only files were not installed.** Two complete families were left out because
   nothing in this repository uses them, and one of them is actively dangerous here:

   - **presentation family (7)** — `rules/presentation.md` routed to three `presentation-*`
     agents, which in turn used three `presentation/*` skills. All of them target
     `presentation/**` HTML decks that live only in the upstream repo.
   - **workflows family (14)** — eight `workflows:*` commands plus the six research agents they
     call. Four of those commands rewrite the upstream repo's `README.md` tables; run here they
     would overwrite this repository's own README.

   Each family was dropped whole, so no orphaned agent, rule or skill reference is left
   behind — `grep -r` across `.claude/` finds no mention of any omitted name. If you want any
   of it back, take it from the upstream repo at the commit above.

6. **`skills/weather-fetcher/SKILL.md`** — `allowed-tools` changed from a YAML list to a
   space-delimited string. Upstream ships it as a list, which violates the Agent Skills spec
   (`[allowed-tools-format] Allowed-tools must be a space-delimited string`). This repository's
   CI (`validate-and-test.yml`, `persona-fidelity.yml`) validates `prebuilt/`, `scripts/` and
   `tests/` — not `.claude/skills/` — so nothing here would have caught it; the fix is carried
   over anyway so the installed files are spec-clean. `agent-browser` already used the string
   form upstream.

   Note: `user-invocable` (on `weather-fetcher` and `time-skill`) is a Claude Code extension and
   is not in the spec's recognised field set, so a spec validator emits an `[unknown-field]`
   warning for it. The field is functional in Claude Code, so it is left as upstream wrote it.

7. **`.claude/.gitignore`** — added `__pycache__/` and `*.pyc`. `hooks.py` is executed by
   `python3`, and any byte-compile of it (or of a future helper module next to it) would
   otherwise drop a `.pyc` straight into a tracked directory.

## Review before relying on it

`settings.json` ships upstream's permission set, which allows `Edit(*)`, `Write(*)` and
`Bash(*)` without prompting (the `ask` list still intercepts `rm`, `chmod`, package managers,
`docker`, `kubectl`, etc.). Tighten `permissions.allow` if you want narrower auto-approval.

## Updating

```bash
git clone --depth 1 https://github.com/shanraisshan/claude-code-best-practice.git /tmp/ccbp
diff -ru .claude /tmp/ccbp/.claude
```

Re-apply the local adaptations above after any sync — including the trim, or the two removed
families will come back.
