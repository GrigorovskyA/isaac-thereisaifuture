# Design

## Context

AGENTS mixed closed permissions with current rules; broad startup reads copied
long experiment history into current context. Latest native pilot acceptance is pending.

## Goals / Non-Goals

Goals: focused reads, one current authority, bounded handoff and preserved history.
Non-goals: training, runtime authority expansion, new MCP/global settings/dependencies.

## Decisions

- Keep durable rules in AGENTS, current state in STATUS, receipts in linked reports.
- Preserve ten originals byte-for-byte under an explicitly inactive history index.
- Resolve read-only context helper paths from its script; support text/JSON, refuse
  STATUS over 12 KB and cap Git entries at 30 with actual count/truncation flag.
- Primary implements/accepts; optional Luna/high executes exact bounded assignments.
- Preserve native gates and pending evidence; never repeat a pilot from stale status.

## Risks / Trade-offs

Routing links retain detail omitted from short summaries. The context helper does
not establish live state or acceptance. File-byte reduction is not a billing claim.
