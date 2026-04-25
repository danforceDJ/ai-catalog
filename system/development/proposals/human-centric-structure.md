# Proposal: Human-Centric Repository Architecture (HCRA)

## Objective
To make the AI Catalog repository easily navigable and understandable for non-developers (e.g., product managers, technical writers, business analysts) while maintaining technical rigor for the automated pipeline.

## Current Pain Points
1. **Technical Jargon:** Folder names like `mcpServers`, `plugins`, and `primitives` are unintuitive for non-technical contributors.
2. **Infrastructure Noise:** Scripts, configuration files, and generated artifacts are mixed with actual content at the root level.
3. **Complex Relationship:** The link between "Primitives" and "Plugins" is explained in `CONTRIBUTING.md` but not visually obvious in the folder structure.

---

## Proposed Structure

### 1. Root-Level Simplification
Clean the root directory to only show the "Human Entry Points" and a single `catalog/` folder.

```text
.
├── catalog/                # All AI Assets (The "What")
├── system/                 # Infrastructure & Tooling (The "How")
├── docs/                   # Marketplace Web Preview
├── README.md               # Overview
├── START_HERE.md           # Simple Onboarding Guide (Non-technical)
└── CONTRIBUTING.md         # Technical Contribution Guide
```

### 2. The `catalog/` Directory (Business-Aligned Naming)
Rename technical folders to match business value and common AI terminology:

| Current Name | Proposed Name | Purpose |
| :--- | :--- | :--- |
| `skills/` | `catalog/capabilities/` | Task-specific instructions (e.g., "Create Jira Ticket"). |
| `agents/` | `catalog/personas/` | Agent profiles and behavior styles. |
| `commands/` | `catalog/prompts/` | Reusable slash commands and text snippets. |
| `mcpServers/` | `catalog/integrations/` | External data sources and tool connections. |
| `templates/` | `catalog/templates/` | Standardized document formats. |
| `plugins/` | `catalog/packages/` | Installable bundles (grouping of the above). |

### 3. The `system/` Directory (Hiding Complexity)
Move all "developer-only" files into a `system/` or `tooling/` folder:
- Move `scripts/` to `system/scripts/`.
- Move `tests/` to `system/tests/`.
- Move `catalog.json` and `.github/plugin/marketplace.json` (tracked artifacts) to `system/artifacts/` or keep them hidden from the main view.
- Move `marketplace.config.json` to `system/config/`.

---

### 4. Simplified "Non-Developer" Workflow
Introduce a three-step path in `START_HERE.md`:

1.  **Draft Your Content:** Use a template in `catalog/templates/` to write your instruction, prompt, or persona in plain Markdown.
2.  **Pick a Category:** Drop your file into the relevant folder in `catalog/` (e.g., `prompts/`).
3.  **Register (Optional):** If you want it installable via the CLI, add its name to a simple list in `catalog/packages/`.

---

## Technical Impact & Transition Plan
- **Script Updates:** Python generators and validators will need to be updated to look in the new paths.
- **Backward Compatibility:** Symlinks or "legacy" path support can be maintained during a transition period.
- **CI/CD:** GitHub/GitLab pipelines must be updated to reflect the new directory layout.
