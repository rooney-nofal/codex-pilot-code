"""LLM client: the only module that talks to the Anthropic API."""  # Docstring describing what this file is for.

from anthropic import Anthropic  # Imports the Anthropic class, the official client for the Claude API.
from dotenv import load_dotenv  # Imports the function that reads the .env file.

load_dotenv()  # Reads .env and loads ANTHROPIC_API_KEY into the program's environment.

MODEL = "claude-sonnet-5-5"  # The model used for every call, stored in one single place.
MAX_TOKENS = 4096  # Maximum length of each reply, to control cost and avoid runaway outputs.

client = Anthropic()  # Creates the API client once; it finds the key in the environment by itself.


def call_llm(system_prompt: str, messages: list, tools: list) -> object:  # The one function the rest of the project calls to talk to the model.
    """Send the conversation to the model and return its raw response."""  # Docstring explaining the function's job.
    return client.messages.create(  # Sends one HTTPS request to the API and returns the model's reply.
        model=MODEL,  # Which model answers.
        max_tokens=MAX_TOKENS,  # The reply length cap defined above.
        system=system_prompt,  # The standing instructions (our system.md text).
        messages=messages,  # The whole conversation history, resent at every call.
        tools=tools,  # The catalog of tools the model is allowed to request.
    )  # Closes the API call; the raw response goes back to whoever called this function. 