# StegTalk Manager Policy

## Purpose

This policy defines how the StegTalk repository continues work when the external chat handoff ends.

## Manager Loop

1. Run `python scripts/verify_managed_completion.py`.
2. Run `python scripts/managed_next_task.py`.
3. Read the returned `next_task`.
4. Execute the highest-priority pending task.
5. Update `STEGTALK_TASK_QUEUE.json` and `STEGTALK_MANAGEMENT_STATE.json`.
6. Keep `production_ready` false until production readiness gates prove otherwise.

## Non-Claims

This management layer does not claim:

- production secure messaging
- production cryptography
- complete StegTalk activation

## Completion Condition

The ecosystem-managed handoff condition is met when the repo contains queue, verifier, manager state, CI workflow, and next-task runner.
