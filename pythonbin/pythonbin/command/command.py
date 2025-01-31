import subprocess


class CommandFailedException(Exception):
    def __init__(self, command, message):
        self.command = command
        self.message = f"Command failed: {command}\n{message}"
        super().__init__(self.message)


def run_command(command, cwd=None):
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=cwd
    )
    if result.returncode != 0:
        raise CommandFailedException(command, result.stderr.decode("utf-8"))
    return result.stdout.decode("utf-8")
