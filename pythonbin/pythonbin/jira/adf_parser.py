from dataclasses import dataclass
from typing import Protocol, Any

import jira.resources


class ADFNode(Protocol):
    version: int | None  # for doc node only
    type: str
    text: str | None  # for nodes that contain text
    level: int | None  # for heading nodes
    attrs: dict[str, Any] | None  # for mention nodes
    language: str | None  # for code block nodes
    url: str | None  # for link nodes
    content: list['ADFNode']

    def get(self, property_name: str, default_value: str) -> str:
        ...


@dataclass
class ADFNodeImpl(ADFNode):
    version: int | None
    type: str
    text: str | None
    level: int | None
    attrs: dict[str, Any] | None
    language: str | None
    url: str | None
    content: list['ADFNode']

    def get(self, property_name: str, default_value: str) -> str:
        return self.__dict__.get(property_name, default_value)


class ADFParser:
    def __init__(self, adf: dict[str, Any]):
        self.adf = adf

    def parse_text_node(self, node: dict[str, Any]) -> str:
        return node.get('text', '')

    def parse_paragraph_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        parsed_content = ''.join([self.parse_node(child) for child in content])
        return f'{parsed_content}\n\n'

    def parse_emoji_node(self, node: dict[str, Any]) -> str:
        attrs = node.get('attrs', {})
        return attrs.get('shortName', '')

    def parse_hard_break_node(self, node: dict[str, Any]) -> str:
        return '\n'

    def parse_heading_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        level = node.get('attrs', {}).get('level', 1)
        parsed_content = ''.join([self.parse_node(child) for child in content])
        return f'{"#" * level} {parsed_content}\n\n'

    def parse_rule_node(self, node: dict[str, Any]) -> str:
        return '---\n\n'

    def parse_list_item_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        parsed_content = ''.join([self.parse_node(child) for child in content])
        return parsed_content

    def parse_bullet_list_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        parsed_content = ''.join([f'- {self.parse_list_item_node(child)}' for child in content])
        return f'{parsed_content}\n'

    def parse_ordered_list_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        parsed_content = ''.join([f'1. {self.parse_list_item_node(child)}\n' for child in content])
        return f'{parsed_content}\n'

    def parse_code_block_node(self, node: dict[str, Any]) -> str:
        content = node.get('content', [])
        code = ''.join([self.parse_node(child) for child in content])
        language = node.get('attrs', {}).get('language', '')
        return f'```{language}\n{code}\n```\n\n'

    def parse_mention(self, node: dict[str, Any]) -> str:
        attrs = node.get('attrs', {})
        _ident = attrs.get('id', '')
        text = attrs.get('text', '')
        return text

    def parse_inline_card_node(self, node: dict[str, Any]) -> str:
        attrs = node.get('attrs', {})
        url = attrs.get('url', '')
        return f'[{url}]({url})'

    def parse_media_group_node(self, node: dict[str, Any]) -> str:
        # Skip media parsing
        return ''

    def parse_media_single_node(self, node: dict[str, Any]) -> str:
        # Skip media parsing
        return ''

    def parse_node(self, node: dict[str, Any]) -> str:
        node_type = node.get('type', '')
        if node_type == 'text':
            return self.parse_text_node(node)
        elif node_type == 'paragraph':
            return self.parse_paragraph_node(node)
        elif node_type == 'emoji':
            return self.parse_emoji_node(node)
        elif node_type == 'hardBreak':
            return self.parse_hard_break_node(node)
        elif node_type == 'heading':
            return self.parse_heading_node(node)
        elif node_type == 'rule':
            return self.parse_rule_node(node)
        elif node_type == 'mention':
            return self.parse_mention(node)
        elif node_type == 'bulletList':
            return self.parse_bullet_list_node(node)
        elif node_type == 'orderedList':
            return self.parse_ordered_list_node(node)
        elif node_type == 'listItem':
            return self.parse_list_item_node(node)
        elif node_type == 'codeBlock':
            return self.parse_code_block_node(node)
        elif node_type == 'inlineCard':
            return self.parse_inline_card_node(node)
        elif node_type == 'mediaGroup':
            return self.parse_media_group_node(node)
        elif node_type == 'mediaSingle':
            return self.parse_media_single_node(node)
        else:
            print(f"Unsupported node type: {node_type}")
            return ''

    def to_markdown(self) -> str:
        content = self.adf.get('content', [])
        markdown = ''.join([self.parse_node(node) for node in content])
        return markdown


def jira_resource_to_markdown(resource: jira.resources.PropertyHolder) -> str:
    """
    Jira client stores comments and descriptions as PropertyHolder objects that adhere to the ADFNode protocol.
    This function converts a PropertyHolder object to markdown.

    :param resource: PropertyHolder object

    :return: Markdown representation of the PropertyHolder object
    """

    node_dict = jira_resource_to_dict(resource)
    parser = ADFParser(node_dict)
    return parser.to_markdown()


def jira_resource_to_dict(resource: jira.resources.PropertyHolder,
                          result: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Jira client stores comments and descriptions as PropertyHolder objects that adhere to the ADFNode protocol.
    This function converts a PropertyHolder object to a dictionary.

    :param resource: PropertyHolder object
    :param result: Dictionary to store the converted object

    :return: Dictionary representation of the PropertyHolder object
    """

    node_type = getattr(resource, "type", None)  # pyright: ignore [reportAttributeAccessIssue]

    node_attrs = {}
    if hasattr(resource, "attrs"):
        node_attrs = jira_resource_to_dict(resource.attrs)  # pyright: ignore [reportAttributeAccessIssue]

    node_text = getattr(resource, "text", None)  # pyright: ignore [reportAttributeAccessIssue]
    node_version = getattr(resource, "version", None)  # pyright: ignore [reportAttributeAccessIssue]
    node_content = getattr(resource, "content", [])  # pyright: ignore [reportAttributeAccessIssue]
    node_level = getattr(resource, "level", None)  # pyright: ignore [reportAttributeAccessIssue]
    node_language = getattr(resource, "language", None)  # pyright: ignore [reportAttributeAccessIssue]
    node_url = getattr(resource, "url", None)  # pyright: ignore [reportAttributeAccessIssue]

    if node_type == "doc":
        result = {
            "version": node_version,
            "type": node_type,
            "content": [],
        }
    else:
        result = {
            "type": node_type,
            "text": node_text,
            "attrs": node_attrs,
            "level": node_level,
            "language": node_language,
            "url": node_url,
            "content": [],
        }

    for child in node_content:
        result["content"].append(jira_resource_to_dict(child, result))

    return result


# Example usage
if __name__ == "__main__":
    import json

    adf_json = '''
    {
      "version": 1,
      "type": "doc",
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Hello "
            },
            {
              "type": "text",
              "text": "world",
              "marks": [
                {
                  "type": "strong"
                }
              ]
            }
          ]
        }
      ]
    }
    '''
    adf = json.loads(adf_json)
    parser = ADFParser(adf)
    markdown = parser.to_markdown()
    print(markdown)
