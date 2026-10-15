"""Git tools: git_status (Palier 2)."""  # Docstring: what this module contains.

import subprocess  # Python's standard way to run external programs like git.

from codexpilot.tools.files import ROOT  # Reuses the same project root as the file tools (one single truth).


def git_status(**kwargs) -> str:  # The tool: reports the repo's current state (takes no real arguments).
    """Show the git status of the project: branch, modified and untracked files."""  # Docstring for humans.
    done = subprocess.run(  # Runs an external command and waits for it to finish.
        ["git", "status", "--short", "--branch"],  # The exact command, as a fixed list: nothing comes from the model.
        cwd=ROOT,  # Runs it inside the project folder, wherever the agent was launched from.
        capture_output=True,  # Captures what the command prints instead of letting it go to the screen.
        text=True,  # Gives us the output as text (str) instead of raw bytes.
        timeout=10,  # Kills the command after 10 seconds, so a stuck git can never freeze the agent.
    )  # Closes the run call; the result is stored in done.

    if done.returncode != 0:  # Exit code 0 means success; anything else means git reported a problem...
        raise RuntimeError(f"git status failed: {done.stderr.strip()}")  # ...so we raise it; run_tool will catch it.

    return done.stdout.strip() or "Working tree clean: nothing modified."  # Returns git's report, or a friendly line if empty.


GIT_STATUS_SCHEMA = {  # The tool's description for the model.
    "name": "git_status",  # The name the model will call.
    "description": (  # When and why to use it.
        "Show the current git status of the project: the branch, modified files, "
        "and untracked files. Use it when the user asks what changed in the repo."
    ),
    "input_schema": {  # The accepted arguments.
        "type": "object",  # One object...
        "properties": {},  # ...with no arguments at all: the command is always the same.
        "required": [],  # Nothing required, since nothing exists.
    },
}  # Closes the schema.