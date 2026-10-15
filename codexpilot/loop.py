"""Agentic loop: call the model, run requested tools, repeat until it answers."""  # Docstring: this module's job.

import subprocess  # Needed to recognize the timeout error raised by run_shell. 

from codexpilot.llm import call_llm  # Our function that talks to the model.
from codexpilot.tools.files import (  # Imports every file tool and its schema from the tools package.
    read_file, READ_FILE_SCHEMA,  # The reading tool and its description.
    list_files, LIST_FILES_SCHEMA,  # The listing tool and its description.
    edit_file, EDIT_FILE_SCHEMA,  # The writing tool and its description.
)  # Closes the grouped import.

from codexpilot.tools.git import git_status, GIT_STATUS_SCHEMA  # Imports the git tool and its description.
from codexpilot.safety import guarded_run_shell  # Imports run_shell WRAPPED in its three safety layers.
from codexpilot.tools.shell import RUN_SHELL_SCHEMA  # Imports the tool's description for the catalog.

TOOL_SCHEMAS = [READ_FILE_SCHEMA, LIST_FILES_SCHEMA, EDIT_FILE_SCHEMA, GIT_STATUS_SCHEMA, RUN_SHELL_SCHEMA]  # The catalog sent to the model: four tools now."git_status":  git_status,  # The model says "git_status" -> we run git_status().
TOOLS_BY_NAME = {  # Maps each tool's name to its Python function: the orchestrator's routing table.
    "read_file": read_file,  # The model says "read_file" -> we run read_file().
    "list_files": list_files,  # The model says "list_files" -> we run list_files().
    "edit_file": edit_file,  # The model says "edit_file" -> we run edit_file().
    "git_status": git_status,  # The model says "git_status" -> we run git_status().
    "run_shell": guarded_run_shell,  # The model says "run_shell" -> it gets the GUARDED version, never the raw one.
}  # Closes the routing table.

MAX_STEPS = 10  # Safety cap: maximum model calls per user message, so the loop can never run forever.


def run_tool(name: str, args: dict) -> tuple[str, bool]:  # Runs one tool safely; returns (output, is_error).
    """Run one tool. Never raises: returns the output and an error flag."""  # Docstring: the safety-net rule.
    func = TOOLS_BY_NAME.get(name)  # Looks up the function by its name; None if unknown.

    if func is None:  # If the model asked for a tool that does not exist...
        return f"Unknown tool: {name}", True  # ...report it as an error message instead of crashing.

    try:  # Tries to run the tool for real.
        return func(**args), False  # Calls the function with the model's arguments; False = no error.
    except FileNotFoundError:  # If the requested file does not exist...
        return f"File not found: {args.get('path', '?')}", True  # ...return a clear message the model can react to.
    except PermissionError as error:  # If our security check refused the path...
        return str(error), True  # ...return the refusal message.
    except subprocess.TimeoutExpired:  # If a shell command ran too long and was killed...
        return "The command took too long and was stopped (timeout).", True  # ...explain it plainly so the model can adapt.
    except Exception as error:  # Any other unexpected problem (last resort)...
        return f"{type(error).__name__}: {error}", True  # ...return the error's name and message, still no crash.


def run_agent_turn(system_prompt: str, history: list) -> str:  # One full turn: from user message to final text answer.
    """Run the agentic loop until the model answers with text, and return that text."""  # Docstring.
    for _ in range(MAX_STEPS):  # Repeats at most MAX_STEPS times (the safety cap).
        response = call_llm(system_prompt, history, TOOL_SCHEMAS)  # Calls the model with prompt + history + tool catalog.

        history.append({"role": "assistant", "content": response.content})  # Saves the model's reply (text or tool request) in the history.

        if response.stop_reason != "tool_use":  # If the model did NOT ask for a tool...
                        return "".join(  # ...its reply is the final answer: glue together every TEXT block it contains.
                block.text  # Takes the text of a block...
                for block in response.content  # ...looking at each block of the reply...
                if block.type == "text"  # ...but keeping ONLY text blocks (skips thinking blocks etc.).
            )  # Closes the join: one clean string, whatever the reply's shape.

        results = []  # Prepares the list of tool results to send back.

        for block in response.content:  # Goes through each block of the model's reply.
            if block.type == "tool_use":  # Only the blocks that are tool requests interest us here.
                output, failed = run_tool(block.name, block.input)  # Runs the requested tool with its arguments.
                results.append({  # Builds the tool_result in the API's expected format.
                    "type": "tool_result",  # Marks this as a tool result.
                    "tool_use_id": block.id,  # Links the result to the exact request (same id).
                    "content": output,  # The tool's output (or the error message).
                    "is_error": failed,  # Tells the model whether the tool failed.
                })  # Closes this tool_result.

        history.append({"role": "user", "content": results})  # Sends the results back as a user message (the API's convention).

    return "I stopped: too many steps for one request."  # Reached only if MAX_STEPS is hit: a readable message, never a crash.