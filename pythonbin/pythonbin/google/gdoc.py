import argparse
import os.path
from dataclasses import dataclass, field
from typing import Any
import re

import google.oauth2.credentials
import googleapiclient.discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file google_token.json.
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_credentials() -> google.oauth2.credentials.Credentials:
    creds = None

    # The file google_credentials.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("google_token.json"):
        creds = Credentials.from_authorized_user_file("google_token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "google_credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("google_token.json", "w") as token:
            token.write(creds.to_json())

    if not isinstance(creds, google.oauth2.credentials.Credentials):
        raise ValueError(
            "Credentials not of type google.oauth2.credentials.Credentials"
        )

    return creds


def get_docs_service(
    creds: google.oauth2.credentials.Credentials,
) -> googleapiclient.discovery.Resource:
    return build("docs", "v1", credentials=creds)


def get_drive_service(
    creds: google.oauth2.credentials.Credentials,
) -> googleapiclient.discovery.Resource:
    return build("drive", "v3", credentials=creds)


@dataclass
class GoogleDocumentComment:
    created_time: str
    author: str
    content: str
    commentAppliesTo: str | None
    isAuthorMe: bool = False
    replies: list["GoogleDocumentComment"] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "GoogleDocumentComment":
        commentAppliesTo = None
        if "quotedFileContent" in data:
            commentAppliesTo = data["quotedFileContent"]["value"]

        return GoogleDocumentComment(
            created_time=data["createdTime"],
            author=data["author"]["displayName"],
            isAuthorMe=data["author"]["me"],
            content=data["content"],
            commentAppliesTo=commentAppliesTo,
            replies=[GoogleDocumentComment.from_dict(reply) for reply in data.get("replies", [])],
        )


@dataclass
class GoogleDocument:
    title: str
    author: str
    document_id: str
    revision_id: str | None = None
    body: list[dict[str, Any]] = field(default_factory=list)
    comments: list[GoogleDocumentComment] = field(default_factory=list)
    lists: dict[str, Any] = field(default_factory=dict)
    markdown_text: str = field(init=False)

    @staticmethod
    def from_dicts(
        document_dict: dict[str, Any], comments: list[dict[str, Any]], author: str
    ) -> "GoogleDocument":
        doc = GoogleDocument(
            title=document_dict["title"],
            author=author,
            document_id=document_dict["documentId"],
            revision_id=document_dict["revisionId"]
            if "revisionId" in document_dict
            else None,
            body=document_dict["body"]["content"],
            lists=document_dict.get("lists") or {},
            comments=[GoogleDocumentComment.from_dict(comment) for comment in comments],
        )
        doc.markdown_text = google_docs_to_markdown(doc)
        return doc


def get_document(
    docs_service: googleapiclient.discovery.Resource,
    drive_service: googleapiclient.discovery.Resource,
    document_id: str,
) -> GoogleDocument:
    try:
        document = docs_service.documents().get(documentId=document_id).execute()  # type: ignore
        comments = (
            drive_service.comments()  # type: ignore
            .list(
                fileId=document_id,
                fields="comments(content,createdTime,author,anchor,quotedFileContent,replies)",
                includeDeleted=False,
            )
            .execute()
        )
        author = (
            drive_service.about()  # type: ignore
            .get(fields="user")
            .execute()
            .get("user", {})
            .get("displayName", "Unknown")
        )
        comments = comments["comments"]
        return GoogleDocument.from_dicts(document, comments, author)
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise error


def google_docs_to_markdown(
    doc: GoogleDocument,
) -> str:
    """
    Convert Google Docs API response to Markdown format.

    Args:
        file_data (dict): The Google Docs API response data

    Returns:
        str: Markdown formatted text
    """
    # Initialize markdown text with frontmatter
    text = f"""---
title: {doc.title}
author: {doc.author}
---

"""

    # Process each content item
    for item in doc.body:
        # Handle tables
        if "table" in item and "tableRows" in item["table"]:
            # Create table header based on first row's cell count
            first_row_cells = item["table"]["tableRows"][0].get("tableCells", [])
            text += "|" + "|".join("" for _ in first_row_cells) + "|\n"
            text += "|" + "|".join("-" for _ in first_row_cells) + "|\n"

            # Process each row
            for row in item["table"]["tableRows"]:
                text_rows = []
                for cell in row.get("tableCells", []):
                    cell_text = []
                    for content in cell.get("content", []):
                        if "paragraph" in content:
                            style_type = (
                                content["paragraph"]
                                .get("paragraphStyle", {})
                                .get("namedStyleType")
                            )
                            for element in content["paragraph"].get("elements", []):
                                styled = style_element(element, style_type)
                                if styled:
                                    cell_text.append(styled.replace("\s+", "").strip())
                    text_rows.append(" ".join(cell_text) if cell_text else "")
                text += f"| {' | '.join(text_rows)} |\n"

        # Handle paragraphs and lists
        if "paragraph" in item and "elements" in item["paragraph"]:
            style_type = (
                item["paragraph"].get("paragraphStyle", {}).get("namedStyleType")
            )
            bullet = item["paragraph"].get("bullet", {})

            # Handle list items
            if "listId" in bullet:
                list_details = doc.lists.get("lists", {}).get(bullet["listId"], {})
                glyph_format = (
                    list_details.get("listProperties", {})
                    .get("nestingLevels", [{}])[0]
                    .get("glyphFormat", "")
                )
                padding = "  " * bullet.get("nestingLevel", 0)

                if glyph_format in ["[%0]", "%0."]:
                    text += f"{padding}1. "
                else:
                    text += f"{padding}- "

            # Process paragraph elements
            for element in item["paragraph"]["elements"]:
                if "textRun" in element and get_content(element):
                    content = get_content(element)
                    if content != "\n":
                        text += style_element(element, style_type) or ""

            # Add appropriate line endings
            if "listId" in bullet:
                if not text.split("\n")[-1].strip().endswith("\n"):
                    text += "\n"
            else:
                text += "\n\n"

    # Clean up extra blank lines between list items
    lines = text.split("\n")
    lines_to_delete = []

    for i in range(3, len(lines)):
        if (
            not lines[i].strip()
            and any(lines[i - 1].strip().startswith(prefix) for prefix in ["1. ", "- "])
            and any(lines[i + 1].strip().startswith(prefix) for prefix in ["1. ", "- "])
        ):
            lines_to_delete.append(i)

    cleaned_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
    text = "\n".join(cleaned_lines)

    # Final cleanup
    text = text.replace("\n\n\n", "\n\n")
    text = re.sub('', '', text)
    return text + "\n"


def style_element(element: dict, style_type: str | None = None) -> str:
    """Apply Markdown styling to a paragraph element."""
    if not element:
        return ""

    content = get_content(element)
    if not content:
        return ""

    # Handle headings
    style_map = {
        "TITLE": f"# {content}",
        "SUBTITLE": f"_{content.strip()}_",
        "HEADING_1": f"## {content}",
        "HEADING_2": f"### {content}",
        "HEADING_3": f"#### {content}",
        "HEADING_4": f"##### {content}",
        "HEADING_5": f"###### {content}",
        "HEADING_6": f"####### {content}",
    }

    if style_type in style_map:
        return style_map[style_type]

    # Handle text styling
    text_style = element.get("textRun", {}).get("textStyle", {})
    if text_style.get("bold") and text_style.get("italic"):
        return f"**_{content}_**"
    elif text_style.get("italic"):
        return f"_{content}_"
    elif text_style.get("bold"):
        return f"**{content}**"

    return content


def get_content(element: dict) -> str:
    """Extract content from a paragraph element."""
    text_run = element.get("textRun", {})
    text = text_run.get("content", "")

    if text_run.get("textStyle", {}).get("link", {}).get("url"):
        return f"[{text}]{text_run['textStyle']['link']['url']}"

    return text


@dataclass
class Args:
    document_ids: list[str] = field(default_factory=list)


def parse_args() -> Args:
    arg_parser = argparse.ArgumentParser(description="Google Docs API")
    arg_parser.add_argument(
        "--document-ids",
        required=True,
        help="Google Docs document IDs",
        action="append",
        default=[],
    )
    args = arg_parser.parse_args()
    return Args(document_ids=args.document_ids)


def main():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    args = parse_args()
    creds = get_credentials()
    docs_service = get_docs_service(creds)
    drive_service = get_drive_service(creds)

    try:
        for document_id in args.document_ids:
            document = get_document(docs_service, drive_service, document_id)
            print(document.markdown_text)
            print("---")
            print("Comments:")
            for comment in document.comments:
                print(
                    f"{comment.created_time} - author is {comment.author} (is author me?: {comment.isAuthorMe})"
                )
                if comment.commentAppliesTo:
                    print(f"Comment applies to this text: {comment.commentAppliesTo}")
                else:
                    print("Not sure where this comment applies to")
                print("Comment content:")
                print(f"{comment.content}")
                if len(comment.replies) > 0:
                    print("Replies:")
                    for reply in comment.replies:
                        print(f"  {reply.created_time} - {reply.author} (is author me?: {reply.isAuthorMe})")
                        print(f"  {reply.content}")
                print("---")
            print("--- end of comments ---")

        print("--- end of document ---")
    except HttpError as err:
        print(err)


if __name__ == "__main__":
    main()
