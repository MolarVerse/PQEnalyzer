"""
Helpers for concise but unambiguous plot labels.
"""

import os
from collections import defaultdict
from pathlib import Path


def unique_path_labels(filenames):
    """
    Return concise path labels that distinguish duplicated basenames.
    """

    filenames = list(filenames)
    if not filenames:
        return []

    path_parts = [_label_parts(filename) for filename in filenames]
    labels = [None] * len(path_parts)

    groups = defaultdict(list)
    for index, parts in enumerate(path_parts):
        groups[_suffix_label(parts, 1)].append((index, parts))

    for members in groups.values():
        if len(members) == 1:
            index, parts = members[0]
            labels[index] = _suffix_label(parts, 1)
            continue

        for index, label in _unique_group_labels(members):
            labels[index] = label

    return labels


def _unique_group_labels(members):
    max_depth = max(len(parts) for _, parts in members)

    for depth in range(2, max_depth + 1):
        labels = [_suffix_label(parts, depth) for _, parts in members]
        if len(set(labels)) == len(labels):
            return [
                (index, label)
                for (index, _), label in zip(members, labels)
            ]

    labels = _deduplicate([
        _suffix_label(parts, max_depth)
        for _, parts in members
    ])

    return [
        (index, label)
        for (index, _), label in zip(members, labels)
    ]


def _label_parts(filename):
    path = Path(filename)
    parts = [part for part in path.parts if part != path.anchor]

    if not parts:
        return [str(filename)]

    return parts


def _suffix_label(parts, depth):
    suffix = parts[-min(depth, len(parts)):]
    return os.path.join(*suffix)


def _deduplicate(labels):
    seen = {}
    unique_labels = []

    for label in labels:
        seen[label] = seen.get(label, 0) + 1
        if seen[label] == 1:
            unique_labels.append(label)
        else:
            unique_labels.append(f"{label} ({seen[label]})")

    return unique_labels
