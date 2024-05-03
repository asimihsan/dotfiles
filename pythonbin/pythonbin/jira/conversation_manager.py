from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from pythonbin.jira.llm_client import LLMClient

system_message = """You are a helpful assistant designed to output Markdown within JSON.

Answer at an expert-level as a role whose expertise is suited to the question and state your role by saying "As a [role], ...". You are also trained in critical thought and analysis. Have strong opinions but justify them using evidence-based arguments. Predict my next questions and concerns and preemptively address them. Prefer natural flowing paragraphs without sub heading and bullets that are edited for clarity, pedagogy, and in an inverted pyramid writing style. Avoid bullet points except for enumerations."""

initial_user_message = """
I need your help generating Jira epics and child issues for my project. To start, I'll provide you with a few exemplar Jira issue keys. Please fetch the details of each issue and analyze them to understand their structure, format, and content.

Feel free to ask me for more exemplar issues if you need them to better grasp the patterns.

Once you have a good understanding, you must ask me for more free-form information about the epics and child issues I need. Your task will be to generate new epics and child issues that match my requirements while aligning with the style and structure of the exemplars.

Please continue the conversation and keep asking for more information until you are confident that you have gathered all the necessary details to generate high-quality epics and child issues. Only when you have all the required information and are ready to provide the final output, you should indicate that you are done.

Remember, after you have analyzed the exemplar issues, you MUST ask me for more free-form information about the epics and child issues I need.

Let's start with the first step. Could you please ask me for a list of exemplar Jira issue keys?
"""


class ConversationPhase(Enum):
    COLLECT_ISSUES = 1
    ANALYZE_ISSUES = 2
    COLLECT_REQUIREMENTS = 3
    GENERATE_OUTPUT = 4


@dataclass
class State:
    current_phase: ConversationPhase
    current_method: Callable
    next_phase: Optional[ConversationPhase]
    terminal: bool


class ConversationManager:
    def __init__(self, llm_client: LLMClient):
        self.current_phase = ConversationPhase.COLLECT_ISSUES
        self.llm_client = llm_client
        self.exemplar_issues = []
        self.requirements = []
        self.messages = []
        self.switcher: dict[ConversationPhase, State] = {
            ConversationPhase.COLLECT_ISSUES: State(
                current_phase=ConversationPhase.COLLECT_ISSUES,
                current_method=self.prompt_for_issues,
                next_phase=ConversationPhase.ANALYZE_ISSUES,
                terminal=False,
            ),
            ConversationPhase.ANALYZE_ISSUES: State(
                current_phase=ConversationPhase.ANALYZE_ISSUES,
                current_method=self.analyze_issues,
                next_phase=ConversationPhase.COLLECT_REQUIREMENTS,
                terminal=False,
            ),
            ConversationPhase.COLLECT_REQUIREMENTS: State(
                current_phase=ConversationPhase.COLLECT_REQUIREMENTS,
                current_method=self.collect_requirements,
                next_phase=ConversationPhase.GENERATE_OUTPUT,
                terminal=False,
            ),
            ConversationPhase.GENERATE_OUTPUT: State(
                current_phase=ConversationPhase.GENERATE_OUTPUT,
                current_method=self.generate_output,
                next_phase=None,
                terminal=True,
            ),
        }

    def start_conversation(self):
        # Entry point to start the interaction flow

        continue_conversation = True
        while continue_conversation:
            continue_conversation = self.next_step()

    def next_step(self) -> bool:
        if self.current_phase not in self.switcher:
            raise ValueError(f"Invalid phase: {self.current_phase}")

        state = self.switcher[self.current_phase]
        state.current_method()

        if state.next_phase:
            self.current_phase = state.next_phase
            return True

        if state.terminal:
            self.wrap_up_conversation()
            return False

        raise ValueError(f"Invalid state: {state}")

    def prompt_for_issues(self):
        self.messages.extend(
            [{"role": "system", "content": system_message}, {"role": "user", "content": initial_user_message}]
        )
        initial_messages_length = len(self.messages)
        response = self.llm_client.generate_response(self.messages)
        print(response)

        # Exclude the previous system message and the user's initial message
        self.messages.extend(response.messages[initial_messages_length:])

    def analyze_issues(self):
        # Analyze issues and possibly interact with the user for more info
        pass

    def collect_requirements(self):
        # Prompt the user for more detailed requirements for new issues
        # You might need to design a specific prompt for this
        message = """You have analyzed the exemplar issues and now need more detailed requirements for the new epics and child issues. It is possible that you have already gathered all the necessary details to generate high-quality epics and child issues. If so, you should indicate that you are done. Otherwise, you should keep asking for more information until you are confident that you have gathered all the necessary details.
        
        Signal using a boolean flag `done` to indicate that you have all the required information and are ready to provide the final output. If you are not done, you should ask for more free-form information about the epics and child issues.
        """

        self.messages.extend([{"role": "user", "content": message}])
        initial_messages_length = len(self.messages)
        response = self.llm_client.generate_response(self.messages)
        print(response)

        # Exclude the previous system message and the user's initial message
        self.messages.extend(response.messages[initial_messages_length:])

    def generate_output(self):
        # Generate new epics and child issues based on the collected requirements
        # This step may involve calling another method of the llm_client that deals with generating issues in Jira
        # For demonstration, simply moving to wrap-up phase
        pass

    def wrap_up_conversation(self):
        # Conclude the conversation, summarize actions
        pass
