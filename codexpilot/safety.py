"""Safety layer for run_shell: deny-list, dry-run mode, user confirmation."""  # Docstring: this module's job.

DENY_LIST = (  # Patterns of known-dangerous commands, rejected before anything else happens.
    "rm -rf",  # Recursive force-delete (Linux/Mac): can erase whole folders.
    "rmdir /s",  # Recursive folder delete (Windows).
    "del /f",  # Force-delete files (Windows).
    "format",  # Formats a disk: destroys everything on it.
    "shutdown",  # Turns the computer off.
    "mkfs",  # Creates a filesystem: wipes a disk (Linux).
    "dd if=",  # Low-level disk writing (Linux): can overwrite a whole drive.
    ":(){",  # The classic fork bomb: freezes the machine by spawning endless processes.
    "| sh",  # Piping downloaded text into a shell: the classic remote-code trick.
    "| iex",  # Same trick in PowerShell (Invoke-Expression).
    "push --force",  # Git force-push: can erase remote history.
    "sudo ",  # Administrator rights (Linux/Mac): the agent must never escalate.
)  # Closes the deny-list tuple.

DRY_RUN = False  # The dry-run switch: True = show commands without running them. OFF by default.


def check_command(command: str) -> None:  # Safeguard 1: refuses forbidden commands (returns nothing, or raises).
    """Raise PermissionError if the command matches a forbidden pattern."""  # Docstring.
    lowered = command.lower()  # Lowercases the command, so RM -RF cannot sneak past the check.

    for pattern in DENY_LIST:  # Goes through every forbidden pattern.
        if pattern in lowered:  # If the pattern appears anywhere in the command...
            raise PermissionError(f"Blocked by policy: command contains '{pattern}'.")  # ...refuse, naming the reason.


def confirm_command(command: str) -> bool:  # Safeguard 3: asks the human before running (True = approved).
    """Show the command and ask the user for explicit approval. Default is No."""  # Docstring.
    answer = input(f"Run `{command}` in this project? [y/N] ")  # Shows the exact command and waits for the answer.

    return answer.strip().lower() == "y"  # True ONLY for 'y' or 'Y'; anything else (including Enter) means No.


def guarded_run_shell(command: str) -> str:  # The wrapper the agent will actually use: all three safeguards in order.
    """Run a shell command through the three safety layers, then execute it."""  # Docstring.
    from codexpilot.tools.shell import run_shell  # Imported here (not at the top) to avoid circular-import issues.

    check_command(command)  # Layer 1: deny-list. Raises and stops everything if the command is forbidden.

    if DRY_RUN:  # Layer 2: dry-run mode. If the switch is on...
        return f"[dry-run] Would run: {command}"  # ...describe what would happen and execute nothing.

    if not confirm_command(command):  # Layer 3: human consent. If the user did not type 'y'...
        raise PermissionError("The user declined this command.")  # ...refuse, so the model knows and can adapt.

    return run_shell(command)  # All three layers passed: finally run the real command.