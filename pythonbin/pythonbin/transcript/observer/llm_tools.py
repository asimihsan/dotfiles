from dataclasses import dataclass

from pythonbin.transcript.observer.openai_callable import openai_callable


@dataclass
class Item:
    """For each item to what extent are you ready to make a decision? What are the next steps for each item?
    If there are items that need more evidence, or do not have any evidence and need some, estimate how much time will
    be needed and if there is enough time in the meeting to do so.

    Determine the quality of coverage, how much evidence or consensus has been given for each item, which can be
    considered concluded and which are remaining?
    """

    name: str
    """The name of the item."""

    discussed: bool
    """Whether the item has been discussed yet."""

    done: bool
    """Whether you are ready to make a decision on the item."""

    quality_depth: str
    """How good of a job have they done in discussing the item?"""

    next: str
    """The next steps for me the item. Are we done discussing it? If not, how should I proceed? What questions should I ask? What aspects should I consider?"""

    question1: str
    """If needed, acting as me, what first question should I ask to gather more evidence and increase confidence? If done then ignore. Remember to act like me and use my language."""

    confidence: float
    """Are you sure? This is very important for my career."""


@dataclass
class Response:
    """Holds the collection of analyses, each an analysis of a specific item."""

    time_left: float
    """The time left in the meeting."""

    stage_of_meeting: str
    """The stage of the meeting."""

    overall_impression: str
    """
- **Overall Impression:** [Quick summary emphasizing major strengths and areas for improvement, for example, "Candidate demonstrated comprehensive API design skills and an understanding of scalable systems but needs to enhance their approach to system reliability."]
- **Solution summary:** [A concise overview of the candidate’s proposed system architecture, key components, and their integration to fulfill the requirements of the auction platform.]
- **Depth of solution:** [Assessment of the candidate’s exploration of the problem space and the completeness of their proposed solution.]
    """

    requirements_identification: Item
    """
- **Requirements identification:** [Evaluation of the candidate's effective identification and clarification of both functional and non-functional requirements, reflecting their broad understanding of system design fundamentals.]
    """

    assumptions_made: Item
    """
- **Assumptions made:** [Critique of the assumptions the candidate declared, with emphasis on their suitability and impact on the design, demonstrating the candidate’s ability to engage in a back-and-forth discussion about problem constraints.]
    """

    api_design_and_data_management: Item
    """
- **API design and data management:** [Insight into the proposed API structure, endpoint functionality, error handling, and the candidate’s handling of data entities, schemas, and storage solutions, assessing their ability to break down complex problems and prioritize features based on system needs.]
    """

    architecture: Item
    """
- **Architecture:** [Evaluation of the candidate’s system architecture design, including the choice of components, their interactions, and the rationale behind their selection, reflecting their understanding of system scalability and maintainability.]
    """

    scalability: Item
    """
- **Scalability:** [Assessment of the candidate’s approach to system scalability, including their choice of scaling mechanisms, data partitioning strategies, and load balancing techniques, reflecting their understanding of system performance and growth requirements.]
    """

    observability: Item
    """
- **Observability:** [Evaluation of the candidate’s observability strategy, including logging, monitoring, and alerting mechanisms, assessing their ability to design systems that are easy to debug and maintain.]
    """

    communication_and_cultural_fit: Item
    """
- **Presentation and articulation:** [Feedback on how clearly the candidate communicated their ideas, the rationale behind their design decisions, and their responsiveness to complex scenarios, highlighting their communication skills and ability to adjust communication style.]
- **Engagement and user-centric considerations:** [Assessment of the candidate's interaction with the interviewer, their approach to clarifying user needs, and consideration of user experience in their design, reflecting a balanced, user-centric design philosophy.]
    """

    highest_priority_item: str
    """The highest priority item, and why is it the highest priority?"""

    confidence: float
    """Are you sure? This is very important for my career."""


@openai_callable
class GiveTranscriptAnalysis:
    """Given the prompt, your goal is to analyze the actual meeting transcript below. The meeting may not be finished.
    You are not participating in this meeting. Instead, me and others are participating in the meeting.

    If there are existing numerical estimates or you think using your judgment to make reasonable assumptions and propose
    numerical estimates is useful, use Python code to do so.

    Remember that it is not possible to schedule a further meeting or extend the current session. We must triage and
    prioritize evidence gathering and decision making in the current session.

    Remember in the transcript above, "Me" is me talking and "Other(s)" are one or other people talking. Do not be confused
    and directly try to participate in the meeting.
    """

    def __init__(self):
        self.result: Response | None = None

    def __call__(self, response: Response) -> None:
        self.result = Response
