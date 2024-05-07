import pathlib
import time
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Union, get_type_hints
import inspect

import openai
import tiktoken
from openai.types.beta.threads.runs import RunStep
from typing_extensions import override
from openai import AssistantEventHandler

from pythonbin.transcript.model import Transcript
from pythonbin.transcript.observer.llm_tools import Analysis, describe_callable_taking_pydantic_model
from pythonbin.transcript.observer.observer import Observer


def wait_on_run(client, run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run


class LLMObserver(Observer):
    def __init__(
        self,
        prompt: str | pathlib.Path,
        model_name: str = "gpt-4-turbo",
        max_tokens: int = 2048,
    ):
        self.model_name = model_name
        self.prompt = self._load_prompt(prompt)
        self.max_tokens = max_tokens

        self.client = openai.Client()
        self.instructions = f"{self.prompt}\n\n{self._generate_instructions()}"

        tools = [
            {
                "type": "code_interpreter",
            },
            {
                "type": "function",
                "function": describe_callable_taking_pydantic_model(Analysis),
            },
            {
                "type": "function",
                "function": {
                    "name": "end_run",
                    "description": "End the current run.",
                },
            },
        ]

        self.analysis_fn = Analysis()

        self.assistant = self.client.beta.assistants.create(
            model=self.model_name,
            temperature=0.0,
            name="LLM Observer",
            instructions=self.instructions,
            tools=tools,
        )

    def _load_prompt(self, prompt: Union[str, Path]) -> str:
        if isinstance(prompt, Path):
            with open(prompt, "r") as file:
                return file.read()
        return prompt

    def update(self, payload: Transcript):
        thread = self.client.beta.threads.create()

        transcript_chunks = self._transcript_to_texts(payload)
        for chunk in transcript_chunks:
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=chunk,
            )

        with self.client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            event_handler=EventHandler(),
            max_prompt_tokens=self.max_tokens,
        ) as stream:
            stream.until_done()

    def _transcript_to_texts(self, transcript: Transcript) -> list[str]:
        lines = [f"[{entry.time}] {entry.speaker}: {entry.text}" for entry in transcript.entries]
        lines.append(f"Time elapsed: {transcript.elapsed_time_in_minutes}")
        chunks = chunk_text_by_tokens(lines)
        for i, chunk in enumerate(chunks):
            chunks[i] = f"Here is part of the meeting transcript:\n\n{chunk}"

        chunks[
            len(chunks) - 1
        ] = f"{chunks[len(chunks) - 1]}\n\nEnd of meeting transcript, but note that the meeting may not be finished.\n\nRemember to first discuss next steps, be clear and concrete and specific and decisive."
        return chunks

    def _generate_instructions(self) -> str:
        return """
Act like a helpful senior software engineer. Write in direct, clear, concise language, avoid unnecessary words. You may
skip pronouns and conjunctions if necessary.
        
Given the prompt, your goal is to assess the actual meeting transcript below. The meeting may not be finished.
First determine what items of the meeting need to be covered. Then determine the quality of coverage, how much
evidence or consensus has been given for each item, which can be considered concluded and which are remaining?
For each item to what extent are you ready to make a decision? What are the next steps for each item?
If there are items that need more evidence, or do not have any evidence and need some, estimate how much time will
be needed and if there is enough time in the meeting to do so.

If there are existing numerical estimates or you think using your judgement to make reasonable assumptions and propose
numerical estimates is useful, use Python code to do so.

Remember that it is not possible to schedule a further meeting or extend the current session. We must triage and
prioritize evidence gathering and decision making in the current session.

Remember in the transcript below, "Me" is me talking and "Other(s)" are one or other people talking. Do not be confused
and directly try to participate in the meeting. You are a helpful assistant observer and must analyze the meeting
transcript.

Remember to first discuss next steps, be clear and concrete and specific and decisive. For each, act as if you were me
and using my language and style, propose example statement or question to be made in the meeting.

Remember you must call the function "Analysis" to return your result. Then call "end_run" to end the run. 
"""


def chunk_text_by_tokens(lines: list[str], k=2048) -> list[str]:
    # Join lines with two line feeds
    text = "\n\n".join(lines)

    encoding = tiktoken.get_encoding("cl100k_base")

    # Tokenize the text
    tokens = encoding.encode(text)

    # Initialize variables for chunking
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        # Add the token to the current chunk
        current_chunk.append(token)
        current_length += 1

        # If the current chunk length is equal to or exceeds k, finalize the current chunk
        if current_length >= k:
            chunk_text = encoding.decode(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
            current_length = 0

    # Add the last chunk if it's not empty
    if current_chunk:
        chunk_text = encoding.decode(current_chunk)
        chunks.append(chunk_text)

    return chunks


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print("\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print("\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

    @override
    def on_end(self) -> None:
        print("\nassistant > Ending run.", flush=True)

    @override
    def on_run_step_created(self, run_step: RunStep) -> None:
        print(f"\nassistant > {run_step.type}\n", flush=True)

    @override
    def on_exception(self, exception: Exception) -> None:
        """Fired whenever an exception happens during streaming"""
        print(f"\nassistant > Exception: {exception}", flush=True)

    @override
    def on_timeout(self) -> None:
        """Fires if the request times out"""
        print("\nassistant > Timeout", flush=True)
        raise TimeoutError("Request timed out.")
