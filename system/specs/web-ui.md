# Web UI

The web marketplace is a **fully static single-page app**. No server-side logic at runtime. The entire `catalog.json` is inlined as a JavaScript constant at build time by Jinja2 (`generate_site.py`).

---

## Layout

| Component | Detail |
|---|---|
| **Header** | Robot emoji, title "AI Catalog Marketplace", subtitle |
| **Sticky search bar** | Text input with 100ms debounce; state preserved in `?q=` URL param |
| **Type filter tabs** | All / MCP / Skills / Agents / Prompts / Bundles / Templates; state in `?type=` URL param |
| **Card grid** | CSS `auto-fill` grid, min 420px per card |
| **Footer** | Generated UTC timestamp + GitHub repository link |

---

## Per-Card Content

| Element | Detail |
|---|---|
| **Type badge** | Color-coded pill: purple=mcp, blue=skill, green=agent, pink=prompt, cyan=bundle, amber=template |
| **Name** | Hyperlinked to `github.com/danforceDJ/ai-catalog/tree/main/<repoPath>` |
| **Version** | `vX.Y.Z` |
| **Description** | From catalog entry |
| **Install buttons** | Conditional — see table below |

### Install Button Logic

| Button | Shown when | Action |
|---|---|---|
| `Copy Copilot install` | `install.copilot` is not null | Copies `copilot plugin install <name>@ai-catalog` to clipboard |
| `VSCode install` | `install.vscodeMcpDeeplink` is not null | `<a href="vscode:mcp/install?...">` opens VSCode |
| `Copy raw` | `install.rawFiles` has entries | Opens raw file modal; fetches from `raw.githubusercontent.com` |
| `Download zip` | Always (all items have a zip path) | Direct link to `dl/<name>.zip` |

---

## Raw File Modal

1. Click "Copy raw"
2. A `<dialog>` element opens, fetches the file from:
   ```
   https://raw.githubusercontent.com/danforceDJ/ai-catalog/main/<repoPath>/<file>
   ```
3. Displays in `<pre>` code block
4. "Copy" button copies to clipboard; "Close" dismisses

---

## Search & Filter

### Scoring Algorithm (JavaScript, mirrored in Python for tests)

| Condition | Score added |
|---|---|
| Name **starts with** query | +3 |
| Name **contains** query | +2 |
| Query exactly matches any keyword or tag | +2 |
| Query found in description | +1 |
| No match | 0 (filtered out) |

Results sorted: score descending, then name ascending.

### URL State

Both search and type filter are reflected in the URL:
```
?q=<query>&type=<type>
```

Allows direct linking to filtered views and browser back/forward navigation.

