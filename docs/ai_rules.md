# AI Collaboration Rules for ZFlow

## 1. Purpose

This document defines how AI agents should collaborate on ZFlow.
It overrides all assumptions and defaults.

---

## 2. Mandatory Context

Before making any change, AI MUST read:
- docs/state.md
- docs/user_journey.md
- docs/temp/interface_merge.md

If any conflict exists, docs/state.md has highest priority.

---

## 3. Hard Constraints (DO NOT VIOLATE)

AI MUST NOT:
- Implement features marked as "future" or "mocked" in docs/state.md
- Introduce persistence, auth, or real execution engines unless explicitly instructed
- Modify architecture boundaries without updating docs/state.md first
- Assume production readiness

---

## 4. Allowed Actions

AI MAY:
- Refactor code for clarity without changing behavior
- Improve documentation consistency
- Implement features explicitly listed as "next step" in docs/state.md
- Ask for clarification if scope is ambiguous

---

## 5. Scope Expansion Protocol

If a task implies new capabilities:
1. Stop
2. Propose the change in docs/state.md
3. Wait for human confirmation
4. Only then implement

---

## 6. Default Assumptions

- ZFlow is a task-based demo platform
- Execution is in-memory and simulated
- Clarity > completeness
- Explicit > clever

---

## 7. Failure Handling

If uncertain:
- Do not guess
- Do not invent
- Ask or defer
