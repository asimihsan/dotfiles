import os

from pythonbin.jira.client import JiraClient
from pythonbin.jira.conversation_manager import ConversationManager
from pythonbin.jira.llm_client import LLMClient


def main(server: str, user_email: str, token_auth: str, project_key: str, llm_model: str) -> None:
    client = JiraClient(server=server, user_email=user_email, token_auth=token_auth)
    llm_client = LLMClient(model=llm_model, jira_client=client)
    conversation_manager = ConversationManager(llm_client=llm_client)
    conversation_manager.start_conversation()

    epics = client.get_epics(project_key=project_key)
    for epic in epics:
        print(f"{epic.key}")
        print(epic)
        print("---")


if __name__ == "__main__":
    server = os.environ["JIRA_API_SERVER"]
    user_email = os.environ["JIRA_API_EMAIL"]
    token_auth = os.environ["JIRA_API_TOKEN"]
    project_key = "MDU2"
    llm_model = os.environ["LLM_MODEL"]

    main(server=server, user_email=user_email, token_auth=token_auth, project_key=project_key, llm_model=llm_model)
