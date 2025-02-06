from datetime import datetime, date
from random import randint
from typing import Any

example = {

    "input": {
        "first_visit": {"type": "bool", "default": False}
    },

    "state": {
        "greeting": {
            "type": "str",
            "default": "",
            "calc": {
                "branch": [
                    {"if": {"args": {"first_visit": {}}}, "then": {"text": "Welcome back, "}},
                    {"else": {"text": "Welcome in, "}}
                ]
            }
        },
        "n": {
            "type": "int",
            "default": 0
        },
        "name": {
            "type": "str",
            "default": ""
        }
    },

    "ops": {
        "randomize_number": {
            "args": {},
            "lingo":{
                "set": {"state": {"n": {}}}, 
                "to": {"random": {"randint": {"call": {"a": 1, "b": 100}}}}
            }
        }
    },

    "document": [
        {"heading": {"text": "Example document"}},
        {"block": [
            {"text": "The current date and time is "},
            {"lingo": {"datetime": {"now": {"call": {}}}}},
            {"text": "."},
            {"break": 1},

            {"text": "Please tell us your name: "},
            {"input": {"type": "text"}, "sync": {"state": {"name": {}}}},
            {"break": 1},

            {"text": "Here's a random number: "},
            {"lingo": {"state": {"n": {}}}},
            {"text": "."},
            {"break": 1},
            
            {"button": {"op": {"randomize_number": {}}}, "text": "Randomize"},
            {"break": 1},

            {"lingo": {"state": {"greeting": {}}}},
            {"branch": [
                {"if": {"random": {"randint": {"call": {"a": 0, "b": 1}}}}, "then": {"text": "Silly person"}},
                {"elif": {"state": {"name": {}}}, "then": {"lingo": {"args": {"name": {}}}}},
                {"else": {"text": "Unknown person"}}
            ]},
            {"text": "!"},
            {"break": 2},

            {"text": " Happy "},

            {"switch": {
                "expression": {"date": {"weekday": {"call": {}}}},
                "cases": [
                    {"case": 0, "then": {"text": "Monday"}},
                    {"case": 1, "then": {"text": "Tuesday"}},
                    {"case": 2, "then": {"text": "Wednesday"}},
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

lingo = {
    # built-in functions #
    'bool': {'call': {'func': bool, 'args': {'object': {'type': Any}}}},

    # standard library functions #
    'date': {
        'weekday': {'call': {'func': date.weekday, 'args': {}}}
    },
    'datetime': {
        'now': {'call': {'func': datetime.now, 'args': {}}}
    },
    'random': {
        'randint': {'call': {'func': randint, 'args': {'a': {'type': int}, 'b': {'type': int}}}}
    }
}