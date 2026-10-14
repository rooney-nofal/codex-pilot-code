"""File tools: read_file (Palier 1)."""  # Docstring: what this module contains.

from pathlib import Path  # Path handles file paths safely and cleanly.

ROOT = Path.cwd()  # The project folder the agent is allowed to work in (cwd = current working directory).


def read_file(path: str) -> str:  # The tool itself: takes a relative path, returns the file's text.
    """Read a UTF-8 text file inside the project and return its content."""  # Docstring for humans.
    full_path = (ROOT / path).resolve()  # Joins ROOT + path and resolves it to an absolute, cleaned path.

    if not full_path.is_relative_to(ROOT):  # Security check: is the file still INSIDE the project folder?
        raise PermissionError(f"Access denied: {path} is outside the project folder.")  # Refuses paths like ../../secrets.

    return full_path.read_text(encoding="utf-8")  # Opens the file, reads all its text, and returns it.


READ_FILE_SCHEMA = {  # The tool's description sent to the model: its "job ad".
    "name": "read_file",  # The exact name the model will use to request this tool.
    "description": (  # Explains to the model what the tool does and when to use it.
        "Read a UTF-8 text file from the project and return its content. "
        "Use it before answering any question about a specific file."
    ),
    "input_schema": {  # Describes the arguments the tool accepts, in JSON Schema format.
        "type": "object",  # The arguments arrive as one object (a dictionary).
        "properties": {  # The list of accepted arguments.
            "path": {  # Our single argument: which file to read.
                "type": "string",  # It must be text.
                "description": "Relative path from the project root, e.g. agent.py or prompts/system.md",  # Tells the model the expected format, with examples.
            }
        },
        "required": ["path"],  # The model MUST provide a path; no path, no call.
    },
}  # Closes the schema dictionary.