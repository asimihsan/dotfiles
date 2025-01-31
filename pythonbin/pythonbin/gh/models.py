from urllib.parse import urlparse
from pydantic import BaseModel

class PullRequestURL(BaseModel):
    original_url: str
    owner: str
    repo: str
    number: int

    @classmethod
    def from_url(cls, url: str) -> "PullRequestURL":
        """
        :param url: GitHub PR URL, e.g. https://github.com/LevelHome/LevelServer/pull/3940
        :return: PullRequestURL instance
        """
        elems = urlparse(url)
        if elems.hostname != "github.com":
            raise ValueError(f"Invalid hostname: {elems.hostname}")
        path = elems.path
        path_elems = path.split("/")
        if path_elems[-1] == "files":
            path_elems = path_elems[:-1]
        if len(path_elems) != 5:
            raise ValueError(f"Invalid path: {path}")
        owner = path_elems[1]
        repo = path_elems[2]
        number = int(path_elems[4])
        return cls(original_url=url, owner=owner, repo=repo, number=number)
