# Claude Code 設定使用說明（繁體中文）

這份文件說明 `.claude/` 底下裝了什麼、每個東西的中文名稱是什麼、以及實際要打哪些指令。

安裝來源與英文版說明見 [`README.md`](README.md)。

---

## 一、先讓它生效

`.claude/` 只有在 Claude Code **從專案根目錄啟動**時才會載入。

```bash
cd Master-skill           # 一定要在含有 .claude/ 的目錄
claude                     # 啟動
```

改過 `.claude/settings.json`、`.claude/agents/`、`.claude/commands/`、`.claude/skills/` 之後，
**要重開 Claude Code 才會吃到新設定**（`/agents`、`/skills` 這類選單是啟動時載入的）。

確認有載入成功：

```
/context          # 看目前載入的記憶檔與規則
/agents           # 列出可用的子代理
/skills           # 列出可用的技能
/doctor           # 診斷設定、認證、MCP 連線問題
```

---

## 二、名詞中文對照

這五個詞是整套設定的骨架，先搞懂它們的差別，後面就都通了。

| 英文 | 中文名 | 是什麼 | 放在哪 | 誰來叫它 |
|---|---|---|---|---|
| **Command** | **指令** | 你在對話框打 `/名稱` 觸發的一段流程劇本 | `.claude/commands/*.md` | **你**手動打 |
| **Agent** | **子代理** | 一個獨立的 Claude 分身，有自己的上下文、工具權限、模型 | `.claude/agents/*.md` | 主 Claude 委派 |
| **Skill** | **技能** | 一包「怎麼做某件事」的知識，需要時才載入 | `.claude/skills/*/SKILL.md` | Claude 自動判斷，或你打 `/名稱` |
| **Hook** | **掛鉤** | 事件發生時自動執行的腳本（這裡是播音效） | `.claude/hooks/` | 系統自動 |
| **Rule** | **規則** | 依檔案路徑自動注入的長期記憶 | `.claude/rules/*.md` | 系統自動 |

**一句話分辨 Agent 和 Skill：**
- **子代理**是「請一個人去做」——他有自己的腦袋和權限，做完回報結果。
- **技能**是「給一份說明書」——說明書本身不會做事，是讀的人照著做。

**為什麼要用子代理？** 因為它的上下文是獨立的。叫子代理去讀 50 個檔案找東西，
那 50 個檔案的內容**不會**塞進你的主對話，只有結論會回來。這是省 context 的關鍵。

---

## 三、指令總表

打 `/` 之後選單會出現這些（中文標籤是我加的，方便你一眼認出）：

| 指令 | 中文名 | 做什麼 |
|---|---|---|
| `/weather-orchestrator` | 【示範·三層編排 主控】 | 完整走一次 指令→子代理→技能，產出天氣卡 |
| `/time-command` | 【示範·最簡兩層】 | 最簡版，只走 指令→技能 |

技能也可以直接叫：

| 技能 | 中文名 | 可以直接打 `/` 叫嗎 |
|---|---|---|
| `agent-browser` | 【瀏覽器自動化】 | ✅ 可以 |
| `time-skill` | 【示範·巴基斯坦時間】 | ✅ 可以 |
| `weather-svg-creator` | 【示範·天氣卡繪製】 | ✅ 可以 |
| `weather-fetcher` | 【示範·天氣取數】 | ❌ **不行**（設了 `user-invocable: false`，專供子代理內部使用） |

子代理不能直接打指令叫，要用自然語言請 Claude 委派：

| 子代理 | 中文名 | 怎麼觸發 |
|---|---|---|
| `weather-agent` | 【示範·天氣子代理】 | 說「幫我查杜拜氣溫」，或跑 `/weather-orchestrator` |
| `time-agent-pkt` | 【示範·時間子代理】 | 說「現在巴基斯坦幾點」 |

---

## 四、核心示範：三層編排怎麼跑

這是整套設定最重要的部分。**天氣只是幌子，重點是那個架構。**

```
你打 /weather-orchestrator
   │
   ├─ 第 1 步：指令用 AskUserQuestion 問你要攝氏還華氏
   │
   ├─ 第 2 步：指令委派給 weather-agent 子代理
   │            └─ 子代理身上「預載」了 weather-fetcher 技能
   │               （frontmatter 寫 skills: [weather-fetcher]，一啟動就有）
   │            └─ 子代理照技能的說明去打 Open-Meteo API
   │            └─ 只把「數字＋單位」回報給主流程
   │
   └─ 第 3 步：主流程用 Skill 工具叫 weather-svg-creator 技能
                └─ 畫出 SVG 卡片
                └─ 寫入 orchestration-workflow/weather.svg 與 output.md
```

實際操作：

```
/weather-orchestrator
```

然後選攝氏或華氏，等它跑完。產出會在專案根目錄的 `orchestration-workflow/` 底下。

### 這個示範藏了三個值得抄的設計

**1. 兩種技能載入方式**

| 方式 | 寫法 | 什麼時候用 |
|---|---|---|
| **預載進子代理** | 子代理 frontmatter 寫 `skills: [技能名]` | 這個子代理每次都需要這份知識 |
| **臨時叫用** | 用 `Skill` 工具叫 | 只有特定步驟需要 |

`weather-fetcher` 是預載的，`weather-svg-creator` 是臨時叫的。

**2. 硬性守則（Execution Contract）**

`weather-orchestrator.md` 裡面明文寫死：

> 你**必須**委派給 `weather-agent`。你**禁止**自己用 Bash 或 WebFetch 抓資料、
> 禁止跳過第 1 步、禁止在子代理回報前就叫 `weather-svg-creator`。

這是在防 Claude 「抄近路」。你自己寫工作流時，把不可妥協的規則用這種語氣寫進去。

**3. 失敗即停（Fail-closed）**

> 如果子代理沒有回傳數字和單位，**不准**進第 3 步，直接回報失敗並停止。

沒有這條，Claude 拿不到溫度時可能會自己編一個數字繼續畫圖。
**任何有「取資料 → 用資料」的流程，都應該加這種守則。**

---

## 五、實用元件（不是示範，是真的能用）

### 瀏覽器自動化 `agent-browser`

```
/agent-browser
```

⚠️ **這個技能目前不能用**：它假設系統上有 `agent-browser` 這支 CLI，但那支程式沒有隨附、
SKILL.md 也沒寫怎麼安裝。

**改用 `playwright` MCP**（見下一節），功能重疊而且是現成的。想開網頁就直接說：

```
幫我開 https://example.com 截個圖
```

### MCP 伺服器（`.mcp.json`）

`settings.json` 已設 `"enableAllProjectMcpServers": true`，所以啟動時自動連線，
第一次會用 `npx` 下載，要等一下。

| 伺服器 | 中文名 | 用途 | 怎麼用（直接講白話） |
|---|---|---|---|
| `playwright` | **瀏覽器操控** | 開網頁、填表單、點擊、截圖、抓資料 | 「開這個網址、截圖給我」 |
| `context7` | **即時文件查詢** | 抓套件/框架的**最新**官方文件進 context | 「用 context7 查 Next.js 15 的 App Router 寫法」 |
| `deepwiki` | **GitHub 專案問答** | 問任意 GitHub repo 的架構問題 | 「用 deepwiki 問 vercel/next.js 的路由是怎麼實作的」 |

```
/mcp              # 查看 MCP 連線狀態與可用工具
```

**`context7` 對你這個 repo 特別有用** —— 寫 `tools/clis/*.js` 那些工具時，
可以直接要最新 API 文件，不用靠模型記憶（記憶會過期、會錯）。

### 掛鉤音效 `hooks/`

工作時每個事件播不同音效：工具呼叫、等權限、回應結束、`git commit` 都有專屬聲音。

**需要系統上有播放器**：

| 系統 | 播放器 | 要裝嗎 |
|---|---|---|
| macOS | `afplay` | ❌ 內建 |
| Linux | `paplay` / `aplay` / `ffplay` / `mpg123` 任一 | ✅ 要裝 |
| Windows | `winsound`（Python 內建）/ PowerShell | ❌ 內建 |

沒有播放器時 `hooks.py` 會靜默 exit 0，**不會卡住或報錯**。

檢查你的機器有沒有：

```bash
for p in afplay paplay aplay ffplay mpg123; do
  command -v $p >/dev/null && echo "$p ✅" || echo "$p ❌"
done
```

**開關個別音效** —— 編輯 `.claude/hooks/config/hooks-config.json`，把對應項目改 `true` 就是關閉：

```jsonc
{
  "disableStopHook": true,        // 關掉「回應結束」音效
  "disablePreToolUseHook": true,  // 關掉「工具呼叫前」音效（最吵的一個）
  "disableLogging": true          // 記錄功能，預設關閉
}
```

**全部關掉** —— 改 `.claude/settings.json`：

```jsonc
{ "disableAllHooks": true }
```

**除錯**：把 `disableLogging` 設成 `false`，事件會寫進 `.claude/hooks/logs/hooks-log.jsonl`
（該資料夾已被 gitignore，不會進版控）。

手動測一個事件：

```bash
echo '{"hook_event_name":"Stop"}' | python3 .claude/hooks/scripts/hooks.py
```

完整 30 個事件的說明表在 [`hooks/HOOKS-README.md`](hooks/HOOKS-README.md)。

---

## 六、`settings.json` 每一項在做什麼

| 設定 | 中文說明 | 目前值 |
|---|---|---|
| `permissions.allow` | **免詢問白名單**（24 條） | ⚠️ 含 `Edit(*)`、`Write(*)`、`Bash(*)` |
| `permissions.ask` | **一定要問的黑名單**（22 條） | `rm`、`chmod`、npm/pip/yarn/pnpm、docker、kubectl、wget、kill… |
| `plansDirectory` | 計畫檔存放位置 | `./reports`（第一次用時自動建立） |
| `outputStyle` | 回答風格 | `Explanatory`（會多解釋原理，適合學習） |
| `statusLine` | 輸入框下方狀態列 | 顯示「目錄名 · 分支名」 |
| `attribution` | commit / PR 的署名格式 | Claude 協作者標記 |
| `respectGitignore` | 搜尋時是否略過 gitignore 的檔案 | `true` |
| `env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | context 用到幾 % 才自動壓縮 | `80`（預設更低，這樣設可以撐久一點） |
| `enableAllProjectMcpServers` | 自動啟用 `.mcp.json` 的伺服器 | `true` |
| `disableAllHooks` | 總開關 | `false`（啟用） |
| `hooks` | 30 個事件全部接到 `hooks.py` | — |
| `extraKnownMarketplaces` | 註冊外部技能市集（5 個） | ⚠️ 見下方說明 |
| `enabledPlugins` | 自動啟用的外掛（5 個） | ⚠️ 見下方說明 |

### 那 5 個自動啟用的外掛

這兩個鍵**不是** `claude-code-best-practice` 的一部分，是後來為了跟 `my-frist-project`
一致而刻意加上的——先由另一個獨立的改動加了 `superpowers`，再補上其餘四個。
每次在這個 repo 開 Claude Code，下面 5 個第三方市集的技能都會被載入：

| 市集 | 來源 repo | 啟用的外掛 |
|---|---|---|
| `superpowers-marketplace` | `obra/superpowers-marketplace` | `superpowers` |
| `baoyu-skills` | `JimLiu/baoyu-skills` | `baoyu-skills` |
| `hyperframes` | `heygen-com/hyperframes` | `hyperframes` |
| `antv-infographic` | `antvis/Infographic` | `antv-infographic-skills` |
| `caveman` | `JuliusBrussee/caveman` | `caveman` |

這些是**不受這個專案控制的第三方 repo**——它們出什麼，這裡就載入什麼，而且它們一推新版就會變。
想關掉就把那兩個鍵刪掉；如果只刪 `extraKnownMarketplaces` 裡的某個市集、卻留著
`enabledPlugins` 裡對應的那一行，就會變成「外掛指向一個不存在的市集」，所以**要成對刪**。
這套安裝的其他部分不依賴它們，刪掉照樣能用。

用 `/plugin` 可以查看目前載入了哪些外掛。

### ⚠️ 權限這件事要看一下

`permissions.allow` 裡有 `Edit(*)`、`Write(*)`、`Bash(*)`，意思是**改檔案和跑指令都不會問你**。

好消息是 `ask` 的優先權比 `allow` 高。[官方文件](https://code.claude.com/docs/en/permissions)明講：

> Rules are evaluated in order: **deny, then ask, then allow.** The first match in that order
> determines the outcome, and rule specificity doesn't change the order. […] a matching ask rule
> prompts even when a more specific allow rule also matches the same call.

也就是 **拒絕 > 詢問 > 允許**，而且「規則寫得比較精確」不會讓它插隊。所以就算 `allow` 有 `Bash(*)`，
下面這些還是會攔下來問你：

```
rm / rmdir / shred / unlink / dd / mkfs / fdisk       破壞性檔案操作
chmod / chown                                          權限變更
npm / pip / pip3 / yarn / pnpm                         套件安裝
docker / kubectl / firebase / gcloud                   部署與雲端
wget / kill / killall / pkill                          下載與砍行程
```

**想收緊**：把 `allow` 裡的 `"Bash(*)"` 換成你真的常用的那幾個，例如：

```jsonc
"allow": [
  "Bash(git status)", "Bash(git diff:*)", "Bash(git log:*)",
  "Bash(node:*)", "Bash(ls:*)", "Bash(cat:*)",
  "Read(*)", "Grep(*)", "Glob(*)"
]
```

改完重開 Claude Code。或直接用：

```
/permissions      # 互動式檢視與調整權限
```

**另一種做法**（官方推薦給「想全放行但擋掉幾個」的情境）：`allow` 直接寫 `"Bash"`，
再用 `PreToolUse` 掛鉤攔截你想擋的指令。掛鉤 exit code 2 會在權限規則之前就擋下呼叫，
比維護一長串 `ask` 規則更好管。

---

## 七、常用指令速查

### 每天會用到的

```
/context          看目前 context 用量與載入了哪些記憶
/compact          手動壓縮對話（context 快滿時）
/clear            清空對話重來（保留設定）
/resume           回到之前的某個 session
/rename           幫目前 session 取名字（之後 /resume 好找）
/agents           管理子代理
/skills           管理技能
/mcp              MCP 伺服器狀態
/permissions      權限設定
/doctor           診斷問題
/config           改設定（主題、模型等）
```

### 啟動參數

```bash
claude                          # 一般啟動
claude --continue               # 接續最後一次對話
claude --resume                 # 選一個舊 session 接續
claude -p "問題"                # 一次性提問，不進互動模式
claude --model opus             # 指定模型
claude --permission-mode auto   # 自動模式（少一點權限詢問）
```

### 這個 repo 專用的

```bash
npm run validate                 # 結構驗證（約 9 秒，不呼叫 API）
npm test                         # 完整測試
npm run test:smoke               # 快速煙霧測試
npm run validate:versions        # 版本一致性
pytest                           # Python 測試
```

> 注意：這個 repo 原本**沒有** `.claude/` 目錄，所以這次安裝是從零建立。
> 它自己的 19 個 `SKILL.md` 放在 `prebuilt/`、`masters/` 等目錄，不在 `.claude/skills/` 底下。

---

## 八、照抄這個架構做自己的工作流

想做一個「查資料 → 整理 → 產出」的流程，照這三步做：

### 第 1 步：寫技能（知識）

`.claude/skills/我的技能/SKILL.md`

```markdown
---
name: 我的技能
description: 【中文標籤】 英文描述與觸發詞，讓 Claude 判斷何時該用
allowed-tools: WebFetch(*) Read
---

# 我的技能

## 任務
描述要做什麼、步驟、輸出格式。
```

**格式硬規則**（違反會被 CI 擋下）：

| 欄位 | 規則 |
|---|---|
| `name` | 只能小寫英文、數字、連字號，**必須跟資料夾同名**，不能用中文 |
| `description` | 1–1024 字元，中文可以放這裡 |
| `allowed-tools` | **必須是空白分隔的字串**，❌ 不能寫成 YAML 陣列 |
| SKILL.md | 建議 500 行以內，細節放 `references/` |

> 💡 `allowed-tools` 寫成陣列這個坑，這次安裝就踩到了——upstream 的 `weather-fetcher`
> 原本寫成 YAML list，被 CI 抓出來才修掉。詳見 [`README.md`](README.md) 的在地調整第 6 條。

### 第 2 步：寫子代理（執行者）

`.claude/agents/我的代理.md`

```markdown
---
name: my-agent
description: 【中文標籤】 什麼時候該派這個代理出去
allowedTools: ["Read", "Skill", "WebFetch(*)"]
model: haiku          # haiku 便宜快、sonnet 平衡、opus 最強
maxTurns: 5           # 上限，防止跑不停
memory: project       # 讓它跨 session 記住東西
skills: [我的技能]     # 預載技能，一啟動就有
---

你的職責是……（用第二人稱寫）
```

### 第 3 步：寫指令（流程劇本）

`.claude/commands/我的流程.md`

```markdown
---
description: 【中文標籤】 這個指令做什麼
model: haiku
allowed-tools: [AskUserQuestion, Agent, Skill]
---

# 我的流程

## 執行守則（不可妥協）

你**必須**委派給 `my-agent`。你**禁止**自己動手抓資料。

## 步驟

### 第 1 步：問使用者
用 AskUserQuestion 問……

### 第 2 步：委派
用 Agent 工具，subagent_type: my-agent，prompt: ……

**失敗即停**：如果代理沒回傳有效資料，不准進第 3 步，直接回報失敗。

### 第 3 步：產出
用 Skill 工具叫 ……
```

寫完重開 Claude Code，打 `/我的流程` 就能跑。

---

## 九、疑難排解

| 症狀 | 原因 | 解法 |
|---|---|---|
| `/` 選單沒有新指令 | 沒重開 | 離開 Claude Code 再 `claude` |
| 完全沒載入 `.claude/` | 啟動目錄不對 | `cd` 到含 `.claude/` 的目錄再啟動 |
| 聽不到音效 | 沒有播放器 | 見第五節的偵測指令；macOS 應該內建 `afplay` |
| MCP 工具沒出現 | `npx` 還在下載 | 等一下，或 `/mcp` 看狀態；`node -v` 確認有 Node |
| 一直問權限 | `ask` 清單攔到了 | `/permissions` 調整，或改 `settings.json` |
| 都不問權限，很怕 | `allow` 太寬 | 見第六節「想收緊」 |
| 技能 frontmatter 寫壞了 | 格式硬規則沒守 | 這個 repo 的 CI 不驗證 `.claude/skills/`，要自己照第八節第 1 步檢查 |

### `.gitignore`：這個 repo 不用動

這個 repo 的 `.gitignore` **沒有**忽略 `.claude/`，所以安裝進來的檔案直接就進版控，
不需要做任何白名單設定。安裝時已經用 `git check-ignore` 驗證過。

> 參考：同一套東西裝在 `my-frist-project` 時**有**這個陷阱——那個 repo 為了
> `npx skills add` 的產出，把整個 `.claude/` 都忽略掉了，導致安裝的檔案會被靜默跳過。
> 如果你以後在別的 repo 裝這套，第一件事就是跑
> `git check-ignore -v .claude/settings.json`——有輸出就表示會被忽略，要先改 `.gitignore`。

---

## 十、延伸閱讀

原始 repo 的 README 有 75KB，整理了 Claude Code 全部概念、13 個知名開發工作流的對照表、
以及 83 條來自 Claude Code 作者 Boris Cherny 和社群的實務技巧。**那才是這個 repo 的主體**，
`.claude/` 這些檔案只是可執行的範例。

```bash
git clone --depth 1 https://github.com/shanraisshan/claude-code-best-practice.git /tmp/ccbp
# 然後把它的 tips 段落丟給 Claude，請它針對你的 CLAUDE.md 提改寫建議
```

官方文件：<https://code.claude.com/docs>
