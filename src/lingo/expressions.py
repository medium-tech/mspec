
example = {

    "input": {
        "name": {"type": "str"}
    },

    "document": [
        {"heading": {"text": "Example document"}},
        {"block": [
            {"text": "The current date and time is "},
            # lingo returns a "text" block with the results of the expression (converted to str if necessary)
            {"lingo": "datetime.now()"},
            {"text": "."},
            {"break": 1},

            {"text": "Hello, "},
            {"branch": [
                {"if": "random.randint(0, 1)", "then": {"text": "Silly person"}},
                {"elif": "bool(input.name)", "then": {"lingo": "input.name"}},
                {"else": {"text": "Unknown person"}}
            ]},
            {"text": "!"},
            {"break": 2},

            {"text": "Happy "},

            {"switch": {
                "lingo": "date.weekday()",
                "cases": [
                    {"case": 0, "then": {"text": "Monday"}},
                    {"case": 1, "then": {"text": "Tuesday"}},
                    {"case": 2, "then": {"text": "Humpday"}},
                    {"case": 3, "then": {"text": "Thursday"}},
                    {"case": 4, "then": {"text": "Friday"}},
                ],
                "default": {"text": "Weekend"}
            }},

            {"text": "!"},
            {"break": 1},

            {"text": "This is the culmination of many late nights."},
            {"link": "https://shop.coavacoffee.com/cdn/shop/files/RayosDelSol_Retail_drip_1_680x@2x.png?v=1718728683", "text": "coffee, yum, yum"},
            {"text": "well anyway, enjoy!"},
            {"link": "https://miro.medium.com/v2/resize:fit:1152/format:webp/1*Cvj9qvbKh1LmLSGEwwwZCQ.jpeg"}
        ]}
    ]

}








from dataclasses import dataclass, field, fields, asdict
from typing import Any

#
# comparison
#

@dataclass
class Comparison:
    """Base class for comparison expressions."""

class Equal(Comparison):
    """Class for equality comparison."""
    left: Any
    right: Any

#
# control flow
#

@dataclass
class ControlFlow:
    """Base class for control flow statements."""


class Branch(ControlFlow):
    """Class for if-then branches."""
    condition: Any
    expression: Any

class IfThen(ControlFlow):
    """Base class for branch statements."""
    branches: list = field(default_factory=list)


