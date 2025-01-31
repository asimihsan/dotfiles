from pythonbin.command.command import run_command


def get_ticket_details(ticket):
    return run_command(f"uv run python src/linear_tools/main.py get-issue --issue-id {ticket}", cwd="/Users/asimi/workplace/linear-tools")
    # return run_command(f"jira --comments 100 issue view {ticket} --plain")
