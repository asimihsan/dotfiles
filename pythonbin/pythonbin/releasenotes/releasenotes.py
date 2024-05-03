import argparse
import base64
import collections
import json
import subprocess

import markdown_it.tree
import markdown_it.tree
import pydantic
import semver
from bs4 import BeautifulSoup
from litellm import completion
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from pydantic import BaseModel


class UnknownEncodingError(Exception):
    encoding: str

    def __init__(self, encoding):
        self.encoding = encoding

    def __str__(self):
        return f"Unknown encoding: {self.encoding}"


# Configuration class using Pydantic
class Config(BaseModel):
    litellm_api_base: str = "http://localhost:11434"
    litellm_model: str = "ollama/openhermes:v2.5"
    repo_owner: str = "LevelHome"
    repo_name: str = "LevelServer"
    changelog_filename: str = "CHANGELOG.md"


# Parse arguments and create config
def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate GitHub release notes using LiteLLM.")
    parser.add_argument("--litellm-api-base", default="http://localhost:11434", help="LiteLLM API base URL")
    parser.add_argument("--litellm-model", default="ollama/openhermes:v2.5", help="LiteLLM model to use")
    args = parser.parse_args()
    return Config(
        litellm_api_base=args.litellm_api_base,
        litellm_model=args.litellm_model,
    )


# Function to call GitHub API using `gh` CLI
def gh_api_call(endpoint, method="GET", data=None):
    cmd = ["gh", "api", endpoint, "-X", method]
    if data:
        for key, value in data.items():
            cmd.extend(["-f", f"{key}={value}"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"GitHub API call failed: {result.stderr}")
    return result.stdout


class Release(BaseModel):
    tag_name: str
    body: str


# Function to get the latest release notes and tag
def get_latest_release(config: Config) -> Release:
    endpoint: str = f"repos/{config.repo_owner}/{config.repo_name}/releases/latest"
    response: str = gh_api_call(endpoint)
    response_json = json.loads(response)
    tag = response_json["tag_name"]
    release_notes = response_json["body"]
    return Release(tag_name=tag, body=release_notes)


class Tag(BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    name: str
    commit_sha: str
    semver: semver.Version


# Function to get all tags
def get_all_tags(config: Config) -> list[Tag]:
    endpoint = f"repos/{config.repo_owner}/{config.repo_name}/git/refs/tags"
    response = gh_api_call(endpoint)
    response_json = json.loads(response)

    # response_json is a list of dicts, each dict has a "ref" key with the tag name, e.g. `refs/tags/1.0.0`
    # filter for tags that are semver, e.g. `1.0.0`. Then sort them in reverse order so the latest is first.
    # remember, there is no `v` in front of version.
    # remember, i don't think semver is lexically sortable, so you'll need to use a library to sort them.
    tags: list[Tag] = []
    for tag in response_json:
        tag_name = tag["ref"].split("/")[-1]
        try:
            version = semver.VersionInfo.parse(tag_name)
            tags.append(Tag(name=tag_name, commit_sha=tag["object"]["sha"], semver=version))
        except ValueError:
            pass

    tags.sort(key=lambda x: x.semver, reverse=True)

    return tags


# Function to get the contents of the CHANGELOG.md file
def get_changelog_contents(config: Config, tag: Tag):
    endpoint = f"repos/{config.repo_owner}/{config.repo_name}/contents/{config.changelog_filename}?ref={tag.name}"
    response = gh_api_call(endpoint)
    response_json = json.loads(response)

    content: str
    if response_json["encoding"] == "base64":
        content = base64.b64decode(response_json["content"]).decode("utf-8")
    else:
        raise UnknownEncodingError(response_json["encoding"])

    md = MarkdownIt("commonmark", {"breaks": True}).use(front_matter_plugin).use(footnote_plugin).enable("table")
    tokens = md.parse(content)

    section_tokens: list[markdown_it.tree.Token] = []
    section_header_type: str | None = None
    for token, next_token in zip(tokens, tokens[1:]):
        if token.type == "heading_open":
            child = next_token
            heading_text = child.content
            if heading_text.startswith(tag.name):
                section_header_type = token.tag
                section_tokens.append(token)
            elif section_header_type is not None:
                # If section_header_type is not None, we might be in the section for a release, or we might be looking
                # at the heading for the next release.
                if child.tag == section_header_type:
                    # We're looking at the heading of the next release, so we're done.
                    break

                # We're looking at the section for a release.
                section_tokens.append(token)
        elif section_header_type is not None:
            section_tokens.append(token)

    if len(section_tokens) == 0:
        raise Exception(f"Could not find heading for tag {tag.name}")

    renderer = MDRenderer()
    options = {}
    env = {}
    output_markdown = renderer.render(section_tokens, options, env)

    # Parse response to get CHANGELOG.md contents (you'll need to implement this)
    return output_markdown


def to_tokens(nodes: list[markdown_it.tree.SyntaxTreeNode]) -> list[markdown_it.tree.Token]:
    """Recover the linear token stream."""

    deque: collections.deque[markdown_it.tree.SyntaxTreeNode] = collections.deque()
    deque.extend(nodes)

    tokens: list[markdown_it.tree.Token] = []
    while deque:
        node = deque.popleft()
        if node.token:
            tokens.append(node.token)
        else:
            assert node.nester_tokens
            tokens.append(node.nester_tokens.opening)
            deque.extendleft(node.children)
            tokens.append(node.nester_tokens.closing)

    return tokens


# Function to parse Markdown and extract the relevant section
def parse_changelog_markdown(changelog_markdown, new_version):
    html = markdown(changelog_markdown)
    soup = BeautifulSoup(html, "html.parser")
    # Find the section for the new version (you'll need to implement this)
    return new_version_section


# Function to generate new release notes using LiteLLM
def generate_release_notes(config, latest_release: Release, new_notes):
    messages = [
        {"content": new_notes, "role": "user"},
        {"content": latest_release.body, "role": "system"},
    ]
    response = completion(
        model=config.litellm_model,
        messages=messages,
        api_base=config.litellm_api_base,
    )
    return response["choices"][0]["message"]["content"]


# Main function to run the script
def main():
    config = parse_arguments()
    latest_release: Release = get_latest_release(config)
    tags = get_all_tags(config)
    new_tag = tags[0]  # Assuming the first tag is the latest
    changelog_contents = get_changelog_contents(config, new_tag)
    new_version_section = parse_changelog_markdown(changelog_contents, new_tag)
    new_release_notes = generate_release_notes(config, latest_release, new_version_section)
    print(new_release_notes)


if __name__ == "__main__":
    main()
