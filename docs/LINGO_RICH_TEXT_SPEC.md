# Lingo Rich Text Spec

## Table of Contents

1. [Overview](#overview)
1. [Getting Started](#getting-started)
1. [Top-Level Structure](#top-level-structure)
1. [Block Elements](#block-elements)
   - [Text Element](#text-element)
   - [Link Element](#link-element)
   - [Break Element](#break-element)
   - [List/Value Element](#listvalue-element)
     - [Bullet List](#bullet-list)
     - [Numbered List](#numbered-list)
     - [Table](#table)
1. [Style Object](#style-object)
1. [Full Example](#full-example)

## Overview

The rich text spec (`rich-text-beta-1`) is a sub-spec of the [page spec](./LINGO_SCRIPTING_AND_PAGE_SPEC.md) designed for defining formatted, static text content. Unlike the scripting and page specs, it has no dynamic scripting, no function calls, and no state. All data must be defined as primitives.

It is usable as a `str` field type in an [application spec](./LINGO_MAPP_SPEC.md) model.

**spec name:** `rich-text-beta-1`

**sample files:** `src/mspec/data/lingo/rich-text`

**bootstrap example file:** `python -m mspec example example.json`

## Getting Started

List all built-in rich text specs:

```bash
python -m mspec specs
```

Copy the example rich text spec to your working directory:

```bash
python -m mspec example example.json
```

## Top-Level Structure

A rich text document is a JSON or YAML object with exactly two top-level keys:

```json
{
    "lingo": {
        "version": "rich-text-beta-1"
    },
    "block": []
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `lingo` | object | yes | Metadata object containing `version` |
| `lingo.version` | string | yes | Must be `"rich-text-beta-1"` |
| `block` | list | yes | Ordered list of block elements (may be empty) |

No other top-level keys are permitted.

## Block Elements

The `block` list contains ordered content elements. Each element is an object identified by its primary key.

### Text Element

Renders a run of text, optionally with styling.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `text` | string | yes | The text content |
| `style` | object | no | Optional style overrides (see [Style Object](#style-object)) |

**Example:**
```json
{"text": "Hello, world!"}
```

```json
{"text": "This is bold.", "style": {"bold": true}}
```

### Link Element

Renders a hyperlink.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `link` | string | yes | The URL |
| `text` | string | no | Display text; if omitted the raw URL is shown |

**Example:**
```json
{"link": "https://www.wikipedia.org"}
```

```json
{"link": "https://www.wikipedia.org", "text": "Wikipedia"}
```

### Break Element

Inserts one or more line breaks.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `break` | int | yes | Number of line breaks; must be `>= 1` and `<= 5` |

**Example:**
```json
{"break": 1}
```

### List/Value Element

Renders a list of items. The `type` key must be `"list"`. The optional `display` object controls the rendering format.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `type` | string | yes | Must be `"list"` |
| `value` | list | yes | The list items (see formats below) |
| `display` | object | no | Rendering options (see formats below) |

#### Bullet List

Default rendering when no `display` is specified (or `display.format` is not `"numbers"` or `"table"`).

Each item in `value` must be one of:
- A plain `string`
- A [text element](#text-element) `{"text": "...", "style": {...}}`
- A [link element](#link-element) `{"link": "...", "text": "..."}`

**Example:**
```json
{
    "type": "list",
    "value": [
        "First item",
        {"text": "Bold item", "style": {"bold": true}},
        {"link": "https://example.com", "text": "A link"}
    ]
}
```

#### Numbered List

Set `display.format` to `"numbers"` to render a numbered (ordered) list.

**Example:**
```json
{
    "type": "list",
    "display": {"format": "numbers"},
    "value": [
        "First item",
        "Second item",
        "Third item"
    ]
}
```

#### Table

Set `display.format` to `"table"` to render a table. The `display` object may define either `headers` (for named columns with custom header labels) or `columns` (for a column list with keys as headers).

Each item in `value` must be an object (one row). Each value in the row object must be one of:
- A primitive: `bool`, `int`, `float`, or `string`
- A [text element](#text-element) `{"text": "...", "style": {...}}`
- A [link element](#link-element) `{"link": "...", "text": "..."}`

**Table with named headers:**
```json
{
    "type": "list",
    "display": {
        "format": "table",
        "headers": [
            {"text": "Color", "field": "color"},
            {"text": "Amount", "field": "amount"},
            {"text": "In Stock", "field": "in_stock"}
        ]
    },
    "value": [
        {"color": "red",   "amount": 10, "in_stock": true},
        {"color": "green", "amount": 21, "in_stock": true},
        {"color": "blue",  "amount": 0,  "in_stock": false}
    ]
}
```

**Grid with column list:**
```json
{
    "type": "list",
    "display": {
        "format": "table",
        "columns": ["column1", "column2", "column3"]
    },
    "value": [
        {
            "column1": "Arbitrary text",
            "column2": {"text": "Italic text", "style": {"italic": true}},
            "column3": {"link": "https://example.com", "text": "a link"}
        }
    ]
}
```

## Style Object

The `style` object is used inside [text elements](#text-element) (both as block-level elements and as items inside list values).

| Field | Type | Description |
|-------|------|-------------|
| `bold` | bool | Bold text |
| `italic` | bool | Italic text |
| `underline` | bool | Underlined text |
| `color` | string (enum) | Text color (see options below) |

**Color options:** `red`, `orange`, `yellow`, `green`, `blue`, `indigo`, `violet`, `pink`, `brown`, `black`, `gray`, `white`

No other style fields are permitted.

**Example:**
```json
{"text": "Important!", "style": {"bold": true, "color": "red"}}
```

## Full Example

The built-in example file (`src/mspec/data/lingo/rich-text/example.json`) demonstrates all supported features:

```json
{
    "lingo": {
        "version": "rich-text-beta-1"
    },
    "block": [
        {"text": "Plain text."},
        {"break": 1},
        {"text": "Bold text.", "style": {"bold": true}},
        {"text": "Italic text.", "style": {"italic": true}},
        {"text": "Underlined text.", "style": {"underline": true}},
        {"link": "https://www.wikipedia.org", "text": "Wikipedia"},
        {"link": "https://www.wikipedia.org"},
        {
            "type": "list",
            "value": [
                {"text": "Red",  "style": {"color": "red"}},
                {"text": "Blue", "style": {"color": "blue"}}
            ]
        },
        {
            "type": "list",
            "display": {"format": "numbers"},
            "value": ["First item", "Second item", "Third item"]
        },
        {
            "type": "list",
            "display": {
                "format": "table",
                "headers": [
                    {"text": "Color",    "field": "color"},
                    {"text": "Amount",   "field": "amount"},
                    {"text": "In Stock", "field": "in_stock"}
                ]
            },
            "value": [
                {"color": "red",  "amount": 10, "in_stock": true},
                {"color": "blue", "amount": 0,  "in_stock": false}
            ]
        }
    ]
}
```
