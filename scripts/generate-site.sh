#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$ROOT_DIR/catalog.json"
DOCS_DIR="$ROOT_DIR/docs"
OUTPUT="$DOCS_DIR/index.html"
REPO_URL="https://github.com/danforceDJ/ai-catalog"

if [ ! -f "$CATALOG" ]; then
  echo "catalog.json not found. Run ./scripts/generate-catalog.sh first."
  exit 1
fi

mkdir -p "$DOCS_DIR"

generated_at="$(jq -r '.generated_at' "$CATALOG")"

# --- Build MCP cards HTML ---
mcp_cards=""
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"
  mcp_cards="${mcp_cards}
    <div class=\"card\" id=\"mcp-${name}\">
      <div class=\"card-header\">
        <span class=\"badge badge-mcp\">MCP Server</span>
        <h3><a href=\"${REPO_URL}/tree/main/${path}\" target=\"_blank\" rel=\"noopener\">${name}</a></h3>
      </div>
      <p class=\"description\">${description}</p>
      <div class=\"install\">
        <h4>Install</h4>
        <div class=\"install-tabs\">
          <div class=\"install-block\">
            <span class=\"ide-label\">VSCode</span>
            <code class=\"oneliner\">./scripts/install.sh mcp ${name} --ide vscode --project /path/to/project</code>
          </div>
          <div class=\"install-block\">
            <span class=\"ide-label\">JetBrains</span>
            <code class=\"oneliner\">./scripts/install.sh mcp ${name} --ide jetbrains</code>
          </div>
        </div>
        <a class=\"detail-link\" href=\"${REPO_URL}/tree/main/${path}\" target=\"_blank\" rel=\"noopener\">View config &amp; details &rarr;</a>
      </div>
    </div>"
done < <(jq -c '.mcp[]' "$CATALOG" 2>/dev/null || true)

# --- Build Skills cards HTML ---
skills_cards=""
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  version="$(jq -r '.version // ""' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"
  version_badge=""
  if [ -n "$version" ] && [ "$version" != "null" ]; then
    version_badge=" <span class=\"version\">v${version}</span>"
  fi
  skills_cards="${skills_cards}
    <div class=\"card\" id=\"skill-${name}\">
      <div class=\"card-header\">
        <span class=\"badge badge-skill\">Skill</span>
        <h3><a href=\"${REPO_URL}/tree/main/${path}\" target=\"_blank\" rel=\"noopener\">${name}</a>${version_badge}</h3>
      </div>
      <p class=\"description\">${description}</p>
      <div class=\"install\">
        <h4>Install</h4>
        <div class=\"install-tabs\">
          <div class=\"install-block\">
            <span class=\"ide-label\">VSCode &amp; JetBrains</span>
            <code class=\"oneliner\">./scripts/install.sh skill ${name} --project /path/to/project</code>
          </div>
        </div>
        <a class=\"detail-link\" href=\"${REPO_URL}/blob/main/${path}\" target=\"_blank\" rel=\"noopener\">View skill file &rarr;</a>
      </div>
    </div>"
done < <(jq -c '.skills[]' "$CATALOG" 2>/dev/null || true)

# --- Build Agent cards HTML ---
agents_cards=""
while IFS= read -r item; do
  name="$(jq -r '.name' <<<"$item")"
  description="$(jq -r '.description' <<<"$item")"
  path="$(jq -r '.path' <<<"$item")"
  agents_cards="${agents_cards}
    <div class=\"card\" id=\"agent-${name}\">
      <div class=\"card-header\">
        <span class=\"badge badge-agent\">Agent Profile</span>
        <h3><a href=\"${REPO_URL}/tree/main/$(dirname "$path")\" target=\"_blank\" rel=\"noopener\">${name}</a></h3>
      </div>
      <p class=\"description\">${description}</p>
      <div class=\"install\">
        <h4>Install</h4>
        <div class=\"install-tabs\">
          <div class=\"install-block\">
            <span class=\"ide-label\">All IDEs</span>
            <code class=\"oneliner\">./scripts/install.sh agent ${name} --project /path/to/project</code>
          </div>
        </div>
        <a class=\"detail-link\" href=\"${REPO_URL}/blob/main/${path}\" target=\"_blank\" rel=\"noopener\">View agent profile &rarr;</a>
      </div>
    </div>"
done < <(jq -c '.agents[]' "$CATALOG" 2>/dev/null || true)

# If a section is empty, show a placeholder
empty_section() {
  echo "<p class=\"empty\">No items found.</p>"
}

[ -z "$mcp_cards" ]     && mcp_cards="$(empty_section)"
[ -z "$skills_cards" ]  && skills_cards="$(empty_section)"
[ -z "$agents_cards" ]  && agents_cards="$(empty_section)"

cat > "$OUTPUT" <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Catalog Marketplace</title>
  <meta name="description" content="Company-wide AI configuration marketplace: MCP servers, skills, and agent profiles." />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #f6f8fa;
      --surface: #ffffff;
      --border: #d0d7de;
      --text: #1f2328;
      --muted: #636c76;
      --accent: #0969da;
      --accent-hover: #0550ae;
      --mcp-color: #7c3aed;
      --skill-color: #0969da;
      --agent-color: #1a7f37;
      --radius: 8px;
      --shadow: 0 1px 3px rgba(27,31,36,.12), 0 8px 24px rgba(27,31,36,.06);
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }

    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; color: var(--accent-hover); }

    /* ---------- Header ---------- */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 1.25rem 2rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    header .logo { font-size: 1.75rem; }
    header h1 { font-size: 1.35rem; font-weight: 700; }
    header p  { font-size: .9rem; color: var(--muted); margin-top: .1rem; }

    /* ---------- Main ---------- */
    main { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }

    /* ---------- Nav tabs ---------- */
    .nav-tabs {
      display: flex;
      gap: .5rem;
      margin-bottom: 2rem;
      flex-wrap: wrap;
    }
    .nav-tabs a {
      padding: .45rem 1rem;
      border: 1px solid var(--border);
      border-radius: 2rem;
      font-size: .85rem;
      font-weight: 500;
      color: var(--muted);
      background: var(--surface);
      transition: background .15s, color .15s;
      text-decoration: none;
    }
    .nav-tabs a:hover { background: var(--bg); color: var(--text); text-decoration: none; }

    /* ---------- Section ---------- */
    section { margin-bottom: 3rem; }
    section h2 {
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: 1rem;
      padding-bottom: .4rem;
      border-bottom: 1px solid var(--border);
    }

    /* ---------- Cards ---------- */
    .cards { display: grid; gap: 1rem; grid-template-columns: 1fr; }
    @media (min-width: 640px) {
      .cards { grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); }
    }

    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: .75rem;
    }
    .card-header { display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }
    .card-header h3 { font-size: 1rem; font-weight: 600; }
    .card-header h3 a { color: var(--text); }
    .card-header h3 a:hover { color: var(--accent); }

    .description { color: var(--muted); font-size: .9rem; }

    /* ---------- Badges ---------- */
    .badge {
      display: inline-block;
      font-size: .7rem;
      font-weight: 700;
      letter-spacing: .04em;
      text-transform: uppercase;
      padding: .2em .55em;
      border-radius: 2em;
      flex-shrink: 0;
    }
    .badge-mcp   { background: #ede9fe; color: var(--mcp-color); }
    .badge-skill { background: #dbeafe; color: var(--skill-color); }
    .badge-agent { background: #dcfce7; color: var(--agent-color); }

    .version {
      font-size: .75rem;
      font-weight: 500;
      color: var(--muted);
      margin-left: .3rem;
    }

    /* ---------- Install block ---------- */
    .install h4 { font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: .5rem; }
    .install-tabs { display: flex; flex-direction: column; gap: .5rem; }
    .install-block { display: flex; flex-direction: column; gap: .2rem; }
    .ide-label { font-size: .75rem; font-weight: 600; color: var(--muted); }
    .oneliner {
      display: block;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      font-size: .78rem;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: .35em .65em;
      overflow-x: auto;
      white-space: nowrap;
      color: var(--text);
    }

    .detail-link {
      font-size: .82rem;
      font-weight: 500;
      align-self: flex-start;
      margin-top: .15rem;
    }

    .empty { color: var(--muted); font-size: .9rem; padding: .5rem 0; }

    /* ---------- Footer ---------- */
    footer {
      text-align: center;
      padding: 1.5rem;
      font-size: .8rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
    }
    footer a { color: var(--muted); }
    footer a:hover { color: var(--accent); }
  </style>
</head>
<body>

<header>
  <span class="logo">🤖</span>
  <div>
    <h1>AI Catalog Marketplace</h1>
    <p>MCP servers, skills, and agent profiles for your team</p>
  </div>
</header>

<main>
  <nav class="nav-tabs" aria-label="Catalog sections">
    <a href="#mcp-servers">MCP Servers</a>
    <a href="#skills">Skills</a>
    <a href="#agent-profiles">Agent Profiles</a>
    <a href="${REPO_URL}" target="_blank" rel="noopener">GitHub &rarr;</a>
  </nav>

  <section id="mcp-servers">
    <h2>🔌 MCP Servers</h2>
    <div class="cards">
${mcp_cards}
    </div>
  </section>

  <section id="skills">
    <h2>🧠 Skills</h2>
    <div class="cards">
${skills_cards}
    </div>
  </section>

  <section id="agent-profiles">
    <h2>🤖 Agent Profiles</h2>
    <div class="cards">
${agents_cards}
    </div>
  </section>
</main>

<footer>
  Generated from <a href="${REPO_URL}/blob/main/catalog.json" target="_blank" rel="noopener">catalog.json</a>
  on ${generated_at} &mdash;
  <a href="${REPO_URL}" target="_blank" rel="noopener">danforceDJ/ai-catalog</a>
</footer>

</body>
</html>
HTML

echo "Generated $OUTPUT"
