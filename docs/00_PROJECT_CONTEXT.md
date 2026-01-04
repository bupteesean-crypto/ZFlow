# Project Context

ZFlow is a production-oriented platform for AI-assisted video generation. The goal is to provide a cohesive workflow from prompt input to final rendered video while keeping responsibilities clearly separated across backend, worker pipeline, and frontend.

## Goals

- Provide a stable API surface for task submission and status tracking.
- Build a prompt-driven generation pipeline with clear stage boundaries.
- Enable parallel development across backend, worker, and frontend teams.

## Non-goals (for this phase)

- Implementing full model orchestration or GPU scheduling.
- Building a complete UI or payment systems.
- Introducing microservices or complex distributed patterns.

## Key principles

- Clarity over cleverness.
- Simple, testable interfaces.
- Prompt assets stored in versioned files, not hard-coded.
