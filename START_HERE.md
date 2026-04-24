# Welcome to the AI Catalog! 🚀

You don't need to be a developer to contribute to our AI toolkit. This guide will show you how to add your own prompts, personas, or instructions in 3 easy steps.

## 🧭 Repository Map
- **`catalog/prompts/`**: Reusable text snippets or "Slash Commands" (e.g., `/write-email`).
- **`catalog/personas/`**: Custom AI personalities or "Agents" (e.g., "Reviewer Agent").
- **`catalog/capabilities/`**: Detailed instructions for specific tasks (e.g., "How to summarize a PR").
- **`catalog/templates/`**: Blank documents you can fill out.
- **`catalog/integrations/`**: Advanced connections to tools like Jira or Slack.

---

## 🛠 How to Add Your Asset

### Step 1: Create your file
Pick a category above and create a new file in that folder.
*   **Tip:** Use one of the examples already in the folder as a template.
*   **Format:** We use **Markdown** (`.md`). It's just like writing a plain text file.

### Step 2: Add "Frontmatter"
At the very top of your file, add a small section between two sets of three dashes `---`. This tells our system what your asset is named and what it does.

```markdown
---
name: my-new-prompt
description: A short description of what this prompt does.
category: productivity
---
# Your Title
Write your prompt or instructions here...
```

### Step 3: Share It
Submit your changes as a **Pull Request** (PR).
*   Our automated **Validator** will check your work for any common mistakes.
*   Once approved and merged, your asset will automatically appear in the [Web Marketplace](https://danforceDJ.github.io/ai-catalog/).

---

## ❓ Need Help?
If you're not sure where to put something, just ask in the #ai-catalog Slack channel or open an issue!
