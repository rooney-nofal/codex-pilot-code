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


IGNORED_DIRS = {".venv", ".git", "__pycache__"}  # Folders we never list: machine-generated noise, not project content.

def list_files(path: str = ".") -> str:  # The tool: lists what a folder contains ("." = project root by default).
    """List the files and folders inside a project directory."""  # Docstring for humans.
    full_path = (ROOT / path).resolve()  # Joins ROOT + path and cleans it, same as in read_file.

    if not full_path.is_relative_to(ROOT):  # Same security check: stay inside the project.
        raise PermissionError(f"Access denied: {path} is outside the project folder.")  # Refuses escapes.

    lines = []  # Will collect one text line per entry found.

    for entry in sorted(full_path.iterdir()):  # Goes through the folder's contents in alphabetical order.
        if entry.name in IGNORED_DIRS:  # Skips the noise folders defined above.
            continue  # Moves on to the next entry.
        if entry.is_dir():  # If this entry is a folder...
            lines.append(f"{entry.name}/")  # ...add its name with a trailing slash, so the model sees it's a folder.
        else:  # Otherwise it's a file...
            lines.append(entry.name)  # ...add just its name.

    return "\n".join(lines) if lines else "(empty directory)"  # Joins all lines into one text block, or says it's empty.


LIST_FILES_SCHEMA = {  # The tool's description for the model.
    "name": "list_files",  # The name the model will call.
    "description": (  # When and why to use it.
        "List the files and folders inside a project directory. "
        "Use it to discover what exists before reading files, or when the user asks what the project contains."
    ),
    "input_schema": {  # The accepted arguments.
        "type": "object",  # Arguments arrive as one object.
        "properties": {  # The argument list.
            "path": {  # Which folder to list.
                "type": "string",  # Text.
                "description": "Relative folder path from the project root. Use '.' for the root itself.",  # Format + the root convention.
            }
        },
        "required": [],  # Empty: path is OPTIONAL — without it, the tool lists the root (the default value ".").
    },
}  # Closes the schema.



def edit_file(path: str, content: str) -> str:  # The tool: writes content into a file (creates it or replaces it).
    """Create a file or overwrite it entirely with the given content."""  # Docstring for humans.
    full_path = (ROOT / path).resolve()  # Joins ROOT + path and cleans it, same pattern as always.

    if not full_path.is_relative_to(ROOT):  # Security check: never write outside the project.
        raise PermissionError(f"Access denied: {path} is outside the project folder.")  # Refuses escapes.

    existed = full_path.exists()  # Remembers whether the file was already there BEFORE we write.

    full_path.parent.mkdir(parents=True, exist_ok=True)  # Creates missing parent folders (e.g. docs/ for docs/note.md).

    full_path.write_text(content, encoding="utf-8")  # Writes the whole content into the file (creates or replaces).

    action = "Updated" if existed else "Created"  # Picks the right word for the confirmation message.

    return f"{action} {path} ({len(content)} characters written)."  # Confirms to the model what happened and how much.


EDIT_FILE_SCHEMA = {  # The tool's description for the model.
    "name": "edit_file",  # The name the model will call.
    "description": (  # When and why to use it — and one warning.
        "Create a new file, or completely replace an existing file's content. "
        "Warning: this overwrites the whole file. To modify an existing file, "
        "read it first with read_file, then send back the full updated content."
    ),
    "input_schema": {  # The accepted arguments.
        "type": "object",  # One object.
        "properties": {  # Two arguments this time.
            "path": {  # Which file to write.
                "type": "string",  # Text.
                "description": "Relative path from the project root, e.g. notes.md or docs/todo.md",  # Format + examples.
            },
            "content": {  # What to write into it.
                "type": "string",  # Text.
                "description": "The complete new content of the file.",  # Makes 'complete' explicit.
            },
        },
        "required": ["path", "content"],  # Both are mandatory: no path or no content, no call.
    },
}  # Closes the schema.  