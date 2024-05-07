import inspect
from dataclasses import dataclass, is_dataclass
from typing import Any, Type, get_type_hints

from deepdiff import DeepDiff


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
            "name": cls.__name__,
            "description": inspect.getdoc(cls),
            "parameters": {"type": "object", "properties": describe_dataclass(response_type)},
        },
    }
    return cls


def describe_dataclass(cls: Type) -> dict[str, Any]:
    """Describe a dataclass class's fields, which may be nested dataclasses."""
    fields_ = get_type_hints(cls)
    properties = {}
    required = []
    for field_name, field_type in fields_.items():
        if is_dataclass(field_type):
            properties[field_name] = describe_dataclass(field_type)["properties"]
        else:
            properties[field_name] = describe_field(field_type)
        if field_name not in cls.__annotations__:
            required.append(field_name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def describe_field(field_type: Type) -> dict[str, Any]:
    """Describe a field type."""
    result = {
        "description": inspect.getdoc(field_type) or "",
    }

    if field_type == str:
        result["type"] = "string"
    elif field_type == int:
        result["type"] = "integer"
    elif field_type == float:
        result["type"] = "number"
    elif field_type == bool:
        result["type"] = "boolean"
    elif is_dataclass(field_type):
        result["type"] = "object"
        result["properties"] = describe_dataclass(field_type)
    else:
        raise ValueError(f"Unsupported field type: {field_type}")

    return result


@dataclass
class Item:
    """Represents an item in the context of a discussion, like a meeting or interview."""

    """The name of the item."""
    name_of_item: str

    """Whether the item has been discussed yet."""
    has_been_discussed_yet: bool

    """Whether you are ready to make a decision on the item."""
    are_you_ready_to_make_a_decision: bool

    """The next steps for the item."""
    next_steps: str


@dataclass
class Response:
    """Holds the a collecton of analyses, each an analysis of a specific item."""

    """The items in the response."""
    items: list[Item]


# @openai_callable
class Analysis:
    """Use this method to perform an analysis of a transcript."""

    def __init__(self):
        self.result: Response | None = None

    def __call__(self, response: Response) -> None:
        self.result = Response


def test_describe_get_current_temperature():
    """
    {
      "type": "function",
      "function": {
        "name": "get_current_temperature",
        "description": "Get the current temperature for a specific location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g., San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["Celsius", "Fahrenheit"],
              "description": "The temperature unit to use. Infer this from the user's location."
            }
          },
          "required": ["location", "unit"]
        }
      }
    }
    :return:
    """

    # === given ===
    @dataclass
    class GetTemperatureRequest:
        """Get the current temperature for a specific location"""

        """The city and state, e.g., San Francisco, CA"""
        location: str

        """The temperature unit to use. Infer this from the user's location."""
        unit: str

    @openai_callable
    class GetTemperature:
        """Get the current temperature for a specific location"""

        def __init__(self):
            self.request: GetTemperatureRequest | None = None

        def __call__(self, request: GetTemperatureRequest) -> None:
            self.request = request

    # === when ===
    result = GetTemperature.openai_function

    # === then ===
    expected = {
        "type": "function",
        "function": {
            "name": "GetTemperature",
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
