import ast
import inspect
import re
from dataclasses import dataclass, is_dataclass
from typing import Any, Type, get_type_hints, Union
from typing import Optional

from deepdiff import DeepDiff


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def openai_callable(cls: Type) -> Type:
    """Decorator to create an OpenAI function schema for a callable class.

    The class must have a __call__ method that takes two arguments, self and a dataclass instance.

    The OpenAI function schema is stored in the openai_function attribute of the class."""
    if not hasattr(cls, "__call__"):
        raise ValueError(f"{cls} does not have a __call__ method.")

    call_signature = inspect.signature(cls.__call__)
    if len(call_signature.parameters) != 2:
        raise ValueError(f"{cls}.__call__ must take two arguments, self and response.")

    response_type = list(call_signature.parameters.values())[1].annotation
    if not is_dataclass(response_type):
        raise ValueError(f"{cls}.__call__ must take a dataclass as the second argument.")

    cls.openai_function = {
        "type": "function",
        "function": {
            "name": camel_to_snake(cls.__name__),
            "description": inspect.getdoc(cls),
            "parameters": describe_dataclass(response_type),
        },
    }
    return cls


def describe_dataclass(cls: Type) -> dict[str, Any]:
    """Describe a dataclass class's fields, which may be nested dataclasses."""
    fields_ = get_type_hints(cls)
    attribute_docs = parse_attribute_docstrings(cls)
    properties = {}
    required = []

    for field_name, field_type in fields_.items():
        description = attribute_docs.get(field_name, "")
        if is_dataclass(field_type):
            properties[field_name] = describe_dataclass(field_type)
        else:
            properties[field_name] = describe_field(field_type, description)
        required.append(field_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def describe_field(field_type: Type, description: str = "") -> dict[str, Any]:
    """Describe a field type with an optional description."""
    result = {"description": description}

    if field_type == str:
        result["type"] = "string"
    elif field_type == int:
        result["type"] = "integer"
    elif field_type == float:
        result["type"] = "number"
    elif field_type == bool:
        result["type"] = "boolean"
    elif is_dataclass(field_type):
        result.update(describe_dataclass(field_type))
    elif field_type == list or getattr(field_type, "__origin__", None) == list:
        inner_type = field_type.__args__[0]
        result["type"] = "array"
        result["items"] = describe_field(inner_type)
    elif field_type == Union and type(None) in field_type.__args__:
        non_none_type = next(t for t in field_type.__args__ if t is not type(None))
        result = describe_field(non_none_type, description)
    else:
        raise ValueError(f"Unsupported field type: {field_type}")

    return result


def add_next_sibling_pointers(tree: ast.AST) -> None:
    """Add a `next_sibling` attribute to each AST node."""

    class NextSiblingTransformer(ast.NodeTransformer):
        def visit(self, node):
            if hasattr(node, "body") and isinstance(node.body, list):
                for i, child in enumerate(node.body):
                    if i + 1 < len(node.body):
                        node.body[i].next_sibling = node.body[i + 1]
                    else:
                        node.body[i].next_sibling = None
                for child in node.body:
                    self.visit(child)
            return node

    NextSiblingTransformer().visit(tree)


def parse_attribute_docstrings(cls: Type) -> dict[str, Optional[str]]:
    """Extract attribute docstrings from a class using the AST module."""
    source = inspect.getsource(cls)
    tree = ast.parse(source)
    add_next_sibling_pointers(tree)
    docstrings = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Extract the target (variable name)
            target = node.targets[0]
            if isinstance(target, ast.Name):
                name = target.id
                # Look for a docstring immediately following the assignment
                if isinstance(node.next_sibling, ast.Expr) and isinstance(node.next_sibling.value, ast.Str):
                    docstrings[name] = node.next_sibling.value.s.strip()
                else:
                    docstrings[name] = None
        elif isinstance(node, ast.AnnAssign):
            name = node.target.id
            if isinstance(node.next_sibling, ast.Expr) and isinstance(node.next_sibling.value, ast.Str):
                docstrings[name] = node.next_sibling.value.s.strip()
            else:
                docstrings[name] = None
    return docstrings


@dataclass
class GetTemperatureRequest:
    """Get the current temperature for a specific location"""

    location: str
    """The city and state, e.g., San Francisco, CA"""

    unit: str
    """The temperature unit to use. Infer this from the user's location"""


@openai_callable
class GetTemperature:
    """Get the current temperature for a specific location"""

    def __init__(self):
        self.request: GetTemperatureRequest | None = None

    def __call__(self, request: GetTemperatureRequest) -> None:
        self.request = request


def test_describe_get_current_temperature():
    # === when ===
    result = GetTemperature.openai_function

    # === then ===
    expected = {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": "Get the current temperature for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city and state, e.g., San Francisco, CA"},
                    "unit": {
                        "type": "string",
                        "description": "The temperature unit to use. Infer this from the user's location",
                    },
                },
                "required": ["location", "unit"],
            },
        },
    }
    diff = DeepDiff(result, expected)
    assert not diff, f"result != expected: {diff}"
