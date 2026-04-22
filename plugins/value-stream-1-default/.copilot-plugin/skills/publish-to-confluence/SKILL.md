---
name: publish-to-confluence
description: Publish a structured specification or document to a Confluence page using the Atlassian MCP server.
version: 1.0.0
license: MIT
compatibility: Requires Atlassian MCP server
metadata:
  author: platform-team
  tags: ["confluence", "documentation", "atlassian"]
---

# publish-to-confluence

## Instructions

1. Accept a document or specification (text, markdown, or file path).
2. Identify the target Confluence space key and parent page title from context or user input.
3. Use the Atlassian MCP `create_page` or `update_page` tool to publish the content.
4. Format content as Confluence-compatible storage format or rich text as required by the API.
5. Return the URL of the published or updated page.

## Example

### Input

```
Publish the following architecture spec to Confluence space ARCH, under parent page "Solution Designs":

# Payment Gateway Integration

## Overview
...
```

### Expected Output

Published to Confluence: `https://your-company.atlassian.net/wiki/spaces/ARCH/pages/123456/Payment+Gateway+Integration`
