import tkinter as tk
from typing import Optional, Callable

from pythonbin.jira.client import JiraClient


def get_epic_wrapper(client: JiraClient) -> Callable[[str], Optional[str]]:
    def get_epic(epic_key: str) -> Optional[str]:
        """
        Retrieve an epic with its child issues from Jira.

        Parameters
        ----------

        epic_key : str
            The key of the epic to retrieve.

        Returns
        -------
        str
            A string representation of the epic and its child issues.
        """
        epic = client.get_epic_by_key(epic_key)
        if epic:
            child_issues_str = "\n".join(
                [f"- {issue.key}: {issue.summary} (type: {issue.issue_type})" for issue in epic.child_issues]
            )
            return f"Epic Key: {epic.key}\nSummary: {epic.summary}\nDescription: {epic.description}\nChild Issues:\n{child_issues_str}"
        else:
            return f"Epic {epic_key} not found."

    return get_epic


from multiprocessing import Process, Queue


def input_window(prompt, queue):
    window = tk.Tk()
    user_input = ""

    def submit_input():
        nonlocal user_input

        user_input = text_input.get("1.0", tk.END).strip()
        queue.put(user_input)
        window.quit()

    # Create the main window
    window.title("User Input")

    # Create the prompt label
    prompt_label = tk.Label(window, text=prompt)
    prompt_label.pack(pady=10)

    # Create the text input field
    text_input = tk.Text(window, wrap=tk.WORD, height=10, width=50)
    text_input.pack()
    text_input.focus_set()

    # Create the submit button
    submit_button = tk.Button(window, text="Submit", command=submit_input)
    submit_button.pack(pady=10)

    # Start the main event loop
    window.mainloop()


def get_user_input(prompt: str) -> str:
    """
    Get free-form user input, for example to get a comma-delimited list of Jira issue IDs, or to get free-form text.

    Parameters
    ----------

    prompt : str
        The prompt to display to the user.

    Returns
    -------
    str
        The user's input as a string.
    """

    # Create a queue to communicate between processes
    queue = Queue()

    # Create a separate process for the input window
    input_process = Process(target=input_window, args=(prompt, queue))
    input_process.start()

    # Wait for the input process to finish
    input_process.join()

    # Get the user input from the queue
    user_input = queue.get()

    return user_input
