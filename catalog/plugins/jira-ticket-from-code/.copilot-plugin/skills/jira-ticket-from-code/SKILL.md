---
name: jira-ticket-from-code
description: Create Jira tickets from TODO/FIXME/BUG code comments by extracting intent and nearby implementation context.
license: MIT
compatibility: Requires Atlassian MCP server
metadata:
  author: platform-team
  version: "1.0.0"
  tags: ["jira", "ticketing", "workflow"]
---

# jira-ticket-from-code

## Instructions

1. Identify `TODO`, `FIXME`, or `BUG` comments from the provided code.
2. Extract:
   - Comment text
   - Surrounding code context (method/class/file) needed to understand the issue
3. Determine the Jira project key from repository/team conventions.
4. Use the Atlassian MCP `create_issue` tool to open a ticket with:
   - Summary based on the comment intent
   - Description including extracted context
   - Appropriate issue type and priority when known
5. Return the created Jira ticket URL.

## Example

### Input (Java)

```java
public class PaymentService {
    public void charge(User user, BigDecimal amount) {
        // TODO: Handle idempotency to prevent duplicate charges on retry
        gateway.charge(user.getId(), amount);
    }
}
```

### Expected Output

Created Jira ticket: `https://your-company.atlassian.net/browse/PAY-1234`
