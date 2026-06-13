# Development Loops

Use bounded 45–90 minute loops.

## Loop steps

1. Observe: read `.hermes/context.md`, `STATUS.md`, current task.
2. Decide: state intended change and non-scope.
3. Act: make the smallest useful change.
4. Verify: run one concrete command/test.
5. Checkpoint: update `STATUS.md`, commit or handoff, name next loop.

## Cap guardrails

- One issue/task per run.
- Inspect ≤ 8 files.
- Modify ≤ 3 files.
- Run ≤ 3 verification commands.
- Store durable context in repo files, not chat.
- Prefer scripts/tests over repeated LLM reasoning.

## Done criteria for each loop

- One artifact changed or created.
- One verification result recorded.
- `STATUS.md` updated.
- Next action written.
