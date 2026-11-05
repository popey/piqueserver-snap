#!/usr/bin/env python3
"""Update the reviewed literal version/source-tag pair without rewriting YAML."""
import argparse
from pathlib import Path
import re


def update(text, tag, check=False):
    if not re.fullmatch(r"v[0-9]+(?:\.[0-9]+){1,3}", tag):
        raise ValueError("expected a numeric upstream release tag")
    versions = list(re.finditer(r"(?m)^version: '([0-9]+(?:\.[0-9]+){1,3})'$", text))
    tags = list(re.finditer(r"(?m)^    source-tag: (v[0-9]+(?:\.[0-9]+){1,3})$", text))
    if len(versions) != 1 or len(tags) != 1 or len(re.findall(r"(?m)^version:", text)) != 1 or len(re.findall(r"(?m)^\s+source-tag:", text)) != 1:
        raise ValueError("expected one literal version/source-tag pair")
    version, source = versions[0], tags[0]
    if source[1] != "v" + version[1]:
        raise ValueError("existing version and source tag disagree")
    if check:
        if tag != source[1]:
            raise ValueError("release tag does not match recipe")
        return text
    def parts(value):
        numbers = tuple(int(x) for x in value.lstrip("v").split("."))
        return numbers + (0,) * (4 - len(numbers))
    if parts(tag) < parts(source[1]):
        raise ValueError("refusing a release downgrade")
    for match, value in sorted([(version, tag[1:]), (source, tag)], key=lambda item: item[0].start(1), reverse=True):
        text = text[:match.start(1)] + value + text[match.end(1):]
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    recipe = Path("snap/snapcraft.yaml")
    result = update(recipe.read_text(), args.tag, args.check)
    if not args.check:
        recipe.write_text(result)
