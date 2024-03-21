import json
from dataclasses import dataclass
from typing import List

from litellm import completion
from litellm.utils import function_to_dict

from pythonbin.jira.client import JiraClient
from pythonbin.jira.llm_functions import get_epic_wrapper, get_user_input


@dataclass
class Response:
    messages: List[dict]
    response: str


class LLMClient:
    def __init__(self, model: str, jira_client: JiraClient):
        self.model = model
        self.jira_client = jira_client
        self.tools = [
            {
                "type": "function",
                "function": function_to_dict(get_epic_wrapper(self.jira_client)),
            },
            {
                "type": "function",
                "function": function_to_dict(get_user_input),
            }
        ]
        print(self.tools)

    def generate_response(self, messages: List[dict]) -> Response:
        messages = messages[:]
        while True:
            response = completion(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.0,
                seed=42,
                response_format={"type": "json_object"},
            )
            print(response)

            finish_reason = response.choices[0].finish_reason
            if finish_reason == "tool_calls":
                messages.append(response.choices[0].message)
                tool_calls = response.choices[0].message.tool_calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    if function_name == "get_epic":
                        epic_key = function_args["epic_key"]
                        print("LLM wants to get epic:", epic_key)
                        epic_response = get_epic_wrapper(self.jira_client)(epic_key)
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": epic_response,
                            }
                        )
                    elif function_name == "get_user_input":
                        print("LLM wants to get user input")
                        prompt = function_args["prompt"]
                        user_input = get_user_input(prompt)
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": user_input,
                            }
                        )
            elif finish_reason == "stop":
                print("LLM has finished")
                messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                })
                return Response(messages=messages, response=response.choices[0].message.content)
            else:
                raise ValueError(f"Unexpected finish_reason: {finish_reason}")
