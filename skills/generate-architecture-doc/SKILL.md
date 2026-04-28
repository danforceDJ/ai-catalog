---
name: generate-architecture-doc
description: Generate a structured solution architecture document from a feature description, ADR, or codebase context.
version: 1.0.0
license: MIT
metadata:
  author: platform-team
  tags: ["architecture", "documentation", "design"]
---

# generate-architecture-doc

## Instructions

1. Accept a feature description, ADR, or relevant codebase context as input.
2. Produce a structured solution architecture document containing:
   - **Overview**: purpose and scope
   - **Architecture Diagram** (described in text/Mermaid)
   - **Components**: each component's role, tech stack, and interfaces
   - **Data Flow**: how data moves between components
   - **Non-Functional Requirements**: scalability, security, availability considerations
   - **Open Questions / Trade-offs**: decisions pending or made with rationale
3. Use existing patterns from the codebase where detectable.
4. Return the document in Markdown format, ready to copy or publish.

## Example

### Input

```
Feature: Add real-time order tracking via WebSockets for the e-commerce platform.
Stack: Node.js backend, React frontend, PostgreSQL, Redis.
```

### Expected Output

```markdown
# Architecture: Real-Time Order Tracking

## Overview
Adds a WebSocket endpoint to stream order status updates to the React frontend...

## Components
- **Order Service** (Node.js): emits status events on order state change
- **WebSocket Gateway** (Node.js + ws): broadcasts events to subscribed clients
- **Redis Pub/Sub**: decouples order service from gateway
...
```
