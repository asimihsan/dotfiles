# llm/client.py
import json
from dataclasses import dataclass
from typing import Any, Callable

from litellm import completion
from litellm.utils import function_to_dict


@dataclass
class Response:
    messages: list[dict]
    response: str


@dataclass
class LLMFunctionTool:
    name: str
    callable: Callable


def get_completion_input(tools: list[LLMFunctionTool]) -> list[dict[str, Any]]:
    """
    Generate the input format for the LLM completion function.

    Parameters
    ----------
    tools : list[LLMFunctionTool]
        A list of LLMFunctionTool objects containing the name and callable function for each tool.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries representing the input format for the LLM completion function.
    """
    return [
        {
            "type": "function",
            "function": function_to_dict(tool.callable),  # type: ignore
        }
        for tool in tools
    ]


def get_tool_lookup(tools: list[LLMFunctionTool]) -> dict[str, Callable]:
    """
    Generate a lookup dictionary for LLM tool functions.

    Parameters
    ----------
    tools : list[LLMFunctionTool]
        A list of LLMFunctionTool objects containing the name and callable function for each tool.

    Returns
    -------
    dict[str, Callable]
        A dictionary mapping tool names to their corresponding callable functions.
    """
    return {tool.name: tool.callable for tool in tools}


class LLMClient:
    def __init__(self, model: str, tools: list[LLMFunctionTool]):
        self.model = model
        self.tools_completion_input = get_completion_input(tools)
        self.tools_lookup = get_tool_lookup(tools)

    def generate_response(self, messages: list[dict]) -> Response:
        messages = messages[:]
        while True:
            response = completion(
                model=self.model,
                messages=messages,
                tools=self.tools_completion_input,
                tool_choice="auto",
                temperature=0.0,
                seed=42,
            )
            print(response.choices[0])

            finish_reason = response.choices[0].finish_reason
            if finish_reason == "tool_calls":
                messages.append(response.choices[0].message)
                tool_calls = response.choices[0].message.tool_calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    if function_name in self.tools_lookup:
                        function_response = self.tools_lookup[function_name](**function_args)
                        print(f"Function: {function_name}, Response: {function_response}")
                    else:
                        raise ValueError(f"Unknown function: {function_name}")

                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        }
                    )
            elif finish_reason == "stop":
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )
                return Response(messages=messages, response=response.choices[0].message.content)
            else:
                raise ValueError(f"Unexpected finish_reason: {finish_reason}")


# llm_functions.py
def get_user_input(prompt: str) -> str:
    """
    Get free-form user input using the console.

    Parameters
    ----------
    prompt : str
        The prompt to display to the user.

    Returns
    -------
    str
        The user's input as a string.
    """
    return input(prompt)

# Define other utility functions here as needed
