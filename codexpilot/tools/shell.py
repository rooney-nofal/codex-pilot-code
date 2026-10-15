"""Shell tool: run_shell (Palier 2). Safety layers are added in safety.py."""  # Docstring: what this module is.

import subprocess  # Python's standard way to run external commands.

from codexpilot.tools.files import ROOT  # Same project root as every other tool: one single truth.

MAX_OUTPUT = 4000  # Maximum characters of output we keep: protects the context window from huge outputs.


def run_shell(command: str) -> str:  # The tool: runs one shell command chosen by the model.
    """Run a shell command inside the project folder and return its output."""  # Docstring for humans.
    done = subprocess.run(  # Runs the command and waits for it to finish.
        command,  # The command string — this time it COMES FROM THE MODEL (that's the danger).
        shell=True,  # Lets the system shell interpret it (pipes, etc.), like a human typing in a terminal.
        cwd=ROOT,  # Containment: the command starts inside the project folder.
        capture_output=True,  # Captures stdout and stderr instead of printing them directly.
        text=True,  # Output as text (str), not bytes.
        timeout=30,  # Containment: kills the command after 30 seconds, so nothing can hang the agent forever.
    )  # Closes the run call.

    output = (done.stdout + done.stderr)[-MAX_OUTPUT:]  # Joins normal + error output, keeps only the LAST 4000 chars.

    return f"exit code {done.returncode}\n{output}"  # Returns the exit code (0 = success) followed by the output.


RUN_SHELL_SCHEMA = {  # The tool's description for the model.
    "name": "run_shell",  # The name the model will call.
    "description": (  # When and why to use it.
        "Run a shell command inside the project folder and return its exit code and output. "
        "Use it to run scripts, tests, or commands the user asks for. "
        "The user must confirm each command before it runs."
    ),
    "input_schema": {  # The accepted arguments.
        "type": "object",  # One object.
        "properties": {  # The argument list.
            "command": {  # The command to execute.
                "type": "string",  # Text.
                "description": "The exact shell command to run, e.g. python --version",  # Format + example.
            }
        },
        "required": ["command"],  # The command is mandatory.
    },
}  # Closes the schema.