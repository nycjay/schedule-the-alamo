# Contributing

Thanks for your interest! Here's how to get started.

## Setup

```bash
uv sync
cp .env.example .env
just serve
```

## Before submitting a PR

```bash
just check
```

This runs ruff (lint), ty (typecheck), and pytest. All three must pass.

## What's in scope

- Bug fixes
- UI/UX improvements
- New filtering or sorting options
- Better rating sources
- Accessibility improvements

## What's out of scope

- Supporting non-Alamo theaters (different API)
- User accounts / multi-user support
- Deployment infrastructure (this is a local tool)

## Style

- Keep it simple. No new dependencies unless unavoidable.
- Match existing patterns — look at how current code does it before adding something new.
- Tests should exercise the HTTP endpoints, not just internal functions.
