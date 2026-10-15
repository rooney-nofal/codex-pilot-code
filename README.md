# CodexPilot Code

A command-line AI agent built from scratch in Python, using only the raw
Anthropic SDK. No agent framework is used: the conversation loop, the tool
dispatch and the safety layer are all implemented in this repository.

The agent reads files, lists directories, writes files, inspects the Git
status of the project and runs shell commands, each one guarded by three
independent safety mechanisms.

## Overview

CodexPilot Code is a terminal assistant in the spirit of Claude Code or
Codex CLI, reduced to its essential mechanism. It demonstrates that an
agent is not a complicated object: it is a language model, a loop, a set
of tools, and a policy that decides what the model is allowed to do.

The program runs as a REPL. The user types a request, the model decides
whether it needs a tool to answer, the loop executes the tool and returns
the result to the model, and the model continues until it has a final
answer. Conversation history is held by the client, which is why the agent
remembers earlier turns within a session.

## Features

- Interactive REPL with client-side conversation history
- Markdown system prompt, editable without touching the Python code
- Five tools: read a file, list files, write a file, read Git status,
  run a shell command
- Generic tool orchestrator: adding a tool requires no change to the loop
- Three-layer safety model around shell execution
- Every tool failure is returned to the model as text, never raised to
  the user as a crash

## Architecture

```
codex-pilot-code/
├── agent.py                 Entry point: the REPL
├── codexpilot/
│   ├── __init__.py
│   ├── llm.py               The only module that talks to the API
│   ├── loop.py              The agentic loop and the tool orchestrator
│   ├── safety.py            Deny-list, dry-run mode, user confirmation
│   └── tools/
│       ├── __init__.py
│       ├── files.py         read_file, list_files, edit_file
│       ├── git.py           git_status
│       └── shell.py         run_shell (raw, never exposed directly)
├── prompts/
│   └── system.md            The agent's identity, tools and rules
├── tech-watch/
│   └── review-and-tech-watch.pdf
├── requirements.txt
├── .env.example
└── .gitignore
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `agent.py` | Reads the system prompt, runs the REPL, owns the history list |
| `codexpilot/llm.py` | Single point of contact with the Anthropic API |
| `codexpilot/loop.py` | Tool catalog, tool routing, multi-step agentic loop |
| `codexpilot/safety.py` | Everything that decides whether a command may run |
| `codexpilot/tools/` | One module per tool family; each tool is a plain function |

The separation is deliberate. Changing the model is a one-line change in
`llm.py`. Changing the agent's behaviour is an edit to `prompts/system.md`
with no code change at all. Adding a tool means writing a function and a
JSON schema, then registering both in `loop.py`.

### The agentic loop

`run_agent_turn` in `codexpilot/loop.py` implements the loop:

1. Send the system prompt, the full history and the tool catalog to the
   model.
2. Append the model's reply to the history.
3. If the model did not request a tool, return its text: the turn is over.
4. Otherwise, execute every requested tool, collect the results, append
   them to the history as a user message, and go back to step 1.

The loop is bounded by `MAX_STEPS = 10`. If the model is still calling
tools after ten iterations, the turn ends with an explicit message rather
than running indefinitely.

The orchestrator itself is generic. Tools are declared in two structures:

- `TOOL_SCHEMAS`, the list of JSON descriptions sent to the model
- `TOOLS_BY_NAME`, a dictionary mapping a tool name to a Python function

`run_tool` looks the name up in that dictionary and calls the function
with the arguments the model produced. No tool is special-cased anywhere
in the loop.

## Tools

| Name | Arguments | Description |
|---|---|---|
| `read_file` | `path` | Returns the text content of a file in the project |
| `list_files` | `path` (optional) | Lists a directory, ignoring `.venv`, `.git` and `__pycache__` |
| `edit_file` | `path`, `content` | Writes a file, creating parent directories if needed |
| `git_status` | none | Returns the current branch and the modified and untracked files |
| `run_shell` | `command` | Runs a shell command in the project directory |

`read_file`, `list_files` and `edit_file` resolve every path against the
project root and refuse any path that escapes it, which blocks directory
traversal such as `../../etc/passwd`.

`edit_file` overwrites the target file completely. The system prompt
instructs the model to read a file before modifying it, so that existing
content is preserved deliberately rather than by accident.

`git_status` runs a fixed command list, `git status --short --branch`.
The model can request it but cannot alter it. It is read-only.

## Safety model

`run_shell` is the only tool whose command is written by the model rather
than by this codebase. It is therefore the only tool that can do real
damage, and it is never registered directly in the orchestrator. The name
`run_shell` is mapped to `guarded_run_shell`, which applies three
mechanisms in order of increasing cost.

**Layer 1 — Deny-list.** The command is lowercased and compared against a
list of forbidden patterns. A match raises `PermissionError` immediately.
Current patterns:

```
rm -rf      rmdir /s    del /f      format      shutdown    mkfs
dd if=      :(){        | sh        | iex       push --force    sudo
```

This layer is deterministic. It does not depend on the model's judgement
and cannot be argued out of its decision.

**Layer 2 — Dry-run mode.** When `DRY_RUN` is set to `True` in
`codexpilot/safety.py`, the agent reports the command it would have run
and executes nothing. This allows a full session to be inspected before
any action is taken. The default is `False`.

**Layer 3 — User confirmation.** The exact command is displayed and the
user must answer `y`. Any other input, including an empty line, is a
refusal, and the refusal is returned to the model so that it can propose
an alternative.

Three independent layers are used rather than one because each can fail on
its own: a deny-list cannot anticipate every dangerous command, and a
human approving many prompts in a row eventually stops reading them.

In addition to these three mechanisms, `run_shell` applies containment:
the command runs with the project directory as its working directory, it
is killed after thirty seconds, and its output is truncated to the last
4000 characters before being sent back to the model.

## Error handling

`run_tool` never raises. Every failure is converted into a text message
and returned to the model with the `is_error` flag set, which allows the
model to explain the problem to the user and to try something else.
Handled cases, from the most specific to the most general:

| Situation | Returned to the model |
|---|---|
| File does not exist | `File not found: <path>` |
| Path escapes the project, command denied, confirmation refused | The refusal message |
| Shell command exceeded its time limit | `The command took too long and was stopped (timeout).` |
| Any other exception | The exception class name and message |

## Requirements

- Python 3.10 or later (developed on 3.14.6)
- Git
- An Anthropic API key with available credit

## Installation

Clone the repository and enter it:

```bash
git clone https://github.com/rooney-nofal/codex-pilot-code.git
cd codex-pilot-code
```

Create and activate a virtual environment.

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The agent reads its API key from a `.env` file at the root of the project.
Copy the provided example and insert your own key:

```bash
cp .env.example .env
```

The file contains a single line:

```
ANTHROPIC_API_KEY=sk-ant-...
```

A key can be created at https://platform.claude.com under API keys. The
`.env` file is listed in `.gitignore` and is never committed.

The model is defined in `codexpilot/llm.py`:

```python
MODEL = "claude-sonnet-5-5"
```

## Usage

Start the agent:

```bash
python agent.py
```

Type a request at the prompt. Type `/quit` to exit.

```
CodexPilot Code is ready. Type /quit to exit.
you > What files are in this project?
agent > The project contains these files: ...

you > Create a file called hello.py that prints Hello World, then run it
Run `python hello.py` in this project? [y/N] y
agent > I created hello.py with print("Hello World") and ran it.
        It exited with code 0 and printed Hello World.

you > /quit
Goodbye!
```

The second example shows the agent chaining two tools in a single turn:
`edit_file` to create the script, then `run_shell` to execute it, with the
confirmation prompt appearing before execution.

## Known behaviour and limitations

- Conversation history lives in memory and is discarded when the process
  exits. Each run starts a new conversation.
- `edit_file` rewrites a file completely; it does not patch a file in
  place.
- The deny-list matches literal substrings. It stops the common
  destructive commands but is not a sandbox, and it is not a substitute
  for running untrusted code in an isolated environment.
- A single turn is capped at ten tool calls.

## Project context

This project was produced for La Plateforme as an exercise in building an
agent without an agent framework. LangChain, LangGraph, smolagents,
LlamaIndex and AutoGen were explicitly excluded, so that the loop, the
tool protocol and the safety policy had to be written and understood
directly.

The work is structured in three stages:

1. An agent that reads: REPL, conversation history, system prompt,
   `read_file`, and the agentic loop.
2. An agent that acts: `list_files`, `edit_file`, `git_status`,
   `run_shell`, a generic orchestrator, the three safety layers, and
   error reporting back to the model.
3. An agent that can be presented: documentation, reproducible setup, and
   a clean repository.

The preliminary review and technology watch, covering existing CLI agents
and the frameworks this project deliberately avoids, is included in
`tech-watch/review-and-tech-watch.pdf`.

## Author

Rooney Nofal