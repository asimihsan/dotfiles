import pathlib

import markdown
from pathlib import Path
from typing import Union
import instructor
from litellm import completion
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from pythonbin.transcript.observer.observer import Observer
from pythonbin.transcript.model import Transcript


class Response(BaseModel):
    text: str


class LLMObserver(Observer):
    def __init__(
        self, prompt: str | pathlib.Path, model_name: str = "claude-3-opus-20240229"
    ):
        self.model_name = model_name
        self.prompt = self._load_prompt(prompt)
        self.client = instructor.from_litellm(completion)

    def _load_prompt(self, prompt: Union[str, Path]) -> str:
        if isinstance(prompt, Path):
            with open(prompt, "r") as file:
                return markdown.markdown(file.read())
        return prompt

    def update(self, payload: Transcript):
        print("received payload")
        transcript_text = self._transcript_to_text(payload)
        print("transcript received")

        instructions = self._generate_instructions(payload)
        system_prompt = f"{self.prompt}\n\n{instructions}"
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                content=system_prompt,
                role="system",
            ),
            ChatCompletionUserMessageParam(
                content=transcript_text,
                role="user",
            ),
        ]

        print("sending messages to LLM")
        response: Response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=1024,
            response_model=Response,
        )
        print("LLM response:")

        print(response)

    def _transcript_to_text(self, transcript: Transcript) -> str:
        return "\n".join(
            f"[{entry.time}] {entry.speaker}: {entry.text}"
            for entry in transcript.entries
        )

    def _generate_instructions(self, transcript: Transcript) -> str:
        # Assuming the meeting duration is provided in the prompt
        # and the agenda or template is also included in the prompt
        # This method will generate further instructions for the model
        # based on the current progress of the meeting and the remaining time
        # ...
        return "Further instructions based on the agenda and remaining time."
