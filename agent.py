"""CodexPilot Code — entry point: the terminal REPL."""  # Docstring: what this file is.

from pathlib import Path  # Imports Path, Python's clean way to work with file paths.

from codexpilot.loop import run_agent_turn  # Imports the agentic loop: it handles the model AND its tools.

SYSTEM_PROMPT = Path("prompts/system.md").read_text(encoding="utf-8")  # Reads system.md once at launch and keeps its text.


def main():  # Groups the whole program in one function, the project's front door.
    print("CodexPilot Code is ready. Type /quit to exit.")  # Welcome line shown once at launch.

    history = []  # The conversation history: OUR program is the memory, the server is stateless.

    while True:  # The REPL loop: repeats forever until we break out of it.
        user_input = input("you › ")  # Shows the prompt, waits, and stores what the user typed.

        if user_input.strip() == "/quit":  # Checks for the exit command (.strip() removes spaces around it).
            print("Goodbye!")  # Farewell message.
            break  # Exits the while loop, which ends the program.

        if user_input.strip() == "":  # If the user just pressed Enter with nothing typed...
            continue  # ...skip the rest and show the prompt again.

        history.append({"role": "user", "content": user_input})  # Adds the user's message to the history.

        answer = run_agent_turn(SYSTEM_PROMPT, history)  # Runs the full agentic loop; it updates the history itself.
        print(f"agent › {answer}")  # Prints the final text answer that came out of the loop.

if __name__ == "__main__":  # Standard Python guard: run main() only when this file is launched directly.
    main()  # Starts the REPL.