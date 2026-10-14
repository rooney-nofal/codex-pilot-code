"""Agentic loop: call the model, run requested tools, repeat until it answers."""  # Docstring: this module's job.

from codexpilot.llm import call_llm  # Our function that talks to the model.
from codexpilot.tools.files import read_file, READ_FILE_SCHEMA  # The tool function and its description.

TOOL_SCHEMAS = [READ_FILE_SCHEMA]  # The catalog of tool descriptions sent to the model.

TOOLS_BY_NAME = {"read_file": read_file}  # Maps a tool's name to its Python function, so we can find it when asked.

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
    except Exception as error:  # Any other unexpected problem (last resort)...
        return f"{type(error).__name__}: {error}", True  # ...return the error's name and message, still no crash.


def run_agent_turn(system_prompt: str, history: list) -> str:  # One full turn: from user message to final text answer.
    """Run the agentic loop until the model answers with text, and return that text."""  # Docstring.
    for _ in range(MAX_STEPS):  # Repeats at most MAX_STEPS times (the safety cap).
        response = call_llm(system_prompt, history, TOOL_SCHEMAS)  # Calls the model with prompt + history + tool catalog.

        history.append({"role": "assistant", "content": response.content})  # Saves the model's reply (text or tool request) in the history.

        if response.stop_reason != "tool_use":  # If the model did NOT ask for a tool...
            return response.content[0].text  # ...its reply is the final answer: return the text, the turn is over.

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