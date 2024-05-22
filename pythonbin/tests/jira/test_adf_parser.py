from typing import Dict, Any

import pytest

from pythonbin.jira.adf_parser import ADFParser


@pytest.fixture
def sample_adf() -> Dict[str, Any]:
    return {
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


def test_parse_text_node(sample_adf):
    parser = ADFParser(sample_adf)
    text_node = sample_adf['content'][0]['content'][0]
    assert parser.parse_text_node(text_node) == "Hello "


def test_parse_paragraph_node(sample_adf):
    parser = ADFParser(sample_adf)
    paragraph_node = sample_adf['content'][0]
    assert parser.parse_paragraph_node(paragraph_node) == "Hello world\n\n"


def test_to_markdown(sample_adf):
    parser = ADFParser(sample_adf)
    assert parser.to_markdown() == "Hello world\n\n"
