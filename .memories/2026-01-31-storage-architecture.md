# Storage Architecture Decision

**ID:** 2026-01-31-storage-architecture
**Date:** 2026-01-31T21:30:00Z
**Type:** architectural-decision
**Context Commit:** 59a4727a551b249eec2416385c00bd18557dfe4b
**Author:** gitsmart-user
**Tags:** storage, collaboration, git-integration

## Decision
Move from local-only `.gitsmart/` storage to git-integrated memory storage for true team collaboration.

## Context
- Current implementation stores memories locally in `.gitsmart/knowledge/`
- Not shared between team members
- Defeats collaborative vision of organizational memory
- Globs concept requires shareable "units of meaning"

## Options Considered
1. **Git Notes**: Attach memories as metadata to commits
2. **Dedicated Branch**: Orphan branch for memories only  
3. **Directory in Main**: `.memories/` tracked in git

## Decision Rationale
Need to implement and test all three approaches to determine best fit for:
- Team collaboration workflow
- Git integration cleanliness  
- Search and retrieval performance
- Merge conflict handling