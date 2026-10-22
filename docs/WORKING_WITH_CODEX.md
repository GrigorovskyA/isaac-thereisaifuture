# Working with this project in Codex

Use plain language. You do not need to choose OpenSpec commands, prepare worker
prompts or manage subagents yourself; the primary agent handles that workflow.

## Continue the current chat

Keep one chat while solving the same task: implementation, an error, checks,
review and corrections belong together. Do not create a chat per command/test.
During an active game experiment use the controlling chat for stop/status requests.
A new chat is not a stop signal and must not start a second game controller.

## Start a fresh chat

Start after an accepted milestone with updated STATUS, or for a separate task.
It is also useful when the old chat repeatedly confuses historical/current state.
Before switching unfinished work, ask for a short STATUS handoff: changes, checks,
remaining work, exact runtime state and blockers. Do not relaunch a failed run.
There is no fixed time or message-count threshold. New chat does not mean a new
model, save, game run, Git checkout or training lineage.

## Starting prompt

Open a new chat in the existing D:\isaac project and use:

> Continue this project from docs/STATUS.md and relevant Git state. Read only the
> context needed for the next unfinished task. First verify any pending experiment
> evidence; do not launch/resume training, create a New Run or extend a budget.

For a specific task replace the first sentence with its goal. State explicit
runtime scope/budget when requesting a new experiment; general continuation is
not authority to repeat an old one. You do not need to paste the previous chat.

The agent can use scripts/Get-ProjectContext.ps1 for the compact handoff.
Full context/history remains in linked files, loaded only when necessary.
