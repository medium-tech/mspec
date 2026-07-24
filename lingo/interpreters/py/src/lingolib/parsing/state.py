from typing import Any

import yaml


class YamlLocationLoader(yaml.SafeLoader):
    pass


YamlLocationLoader.anchors = {}


def get_yaml_line(obj: Any) -> int:
    return YamlLocationLoader.anchors.get(id(obj), -1)


def construct_mapping_with_locations(loader, node):
    loader.flatten_mapping(node)
    mapping = loader.construct_mapping(node)
    # Map the object ID to its start line (1-indexed)
    YamlLocationLoader.anchors[id(mapping)] = node.start_mark.line + 1
    return mapping


def construct_sequence_with_locations(loader, node):
    seq = loader.construct_sequence(node)
    # Map the list ID to its start line
    YamlLocationLoader.anchors[id(seq)] = node.start_mark.line + 1
    return seq


def construct_scalar_with_locations(loader, node):
    val = loader.construct_scalar(node)
    # Map the string/int/bool ID to its start line
    YamlLocationLoader.anchors[id(val)] = node.start_mark.line + 1
    return val


YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping_with_locations
)
YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    construct_sequence_with_locations
)
YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    construct_scalar_with_locations
)
