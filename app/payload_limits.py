"""Safe payload limits checking with bounded traversal.

All checks use iterative traversal or strict depth ceilings to prevent
unbounded recursion and stack overflow attacks.
"""
from __future__ import annotations

import json
from typing import Any


class LimitExceeded(Exception):
    """Raised when payload violates safety limits."""
    pass


def canonical_json_bytes(payload: Any) -> int:
    """Compute byte size of canonical JSON representation.

    Args:
        payload: JSON-serializable object

    Returns:
        byte count of canonical JSON string

    Raises:
        TypeError: if payload is not JSON-serializable
    """
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return len(canonical.encode("utf-8"))
    except (TypeError, ValueError) as e:
        raise TypeError(f"Payload is not JSON-serializable: {e}")


def max_depth(payload: Any, max_safe_depth: int = 100) -> int:
    """Compute maximum nesting depth using bounded iterative traversal.

    Args:
        payload: any Python object
        max_safe_depth: ceiling depth to prevent unbounded recursion

    Returns:
        maximum depth found

    Raises:
        LimitExceeded: if depth exceeds max_safe_depth during traversal
    """
    if not isinstance(payload, (dict, list)):
        return 0

    # Iterative traversal with stack: (obj, current_depth)
    stack = [(payload, 1)]
    max_found = 1

    while stack:
        obj, depth = stack.pop()

        if depth > max_safe_depth:
            raise LimitExceeded(f"Max depth exceeded during traversal (>{max_safe_depth})")

        max_found = max(max_found, depth)

        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    stack.append((value, depth + 1))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    stack.append((item, depth + 1))

    return max_found


def max_list_items(payload: Any, max_safe_items: int = 10_000) -> int:
    """Find the largest list in payload using bounded iterative traversal.

    Args:
        payload: any Python object
        max_safe_items: ceiling to prevent scanning enormous lists

    Returns:
        maximum list length found

    Raises:
        LimitExceeded: if any list exceeds max_safe_items
    """
    if not isinstance(payload, (dict, list)):
        return 0

    # Iterative traversal
    stack = [payload]
    max_found = 0

    while stack:
        obj = stack.pop()

        if isinstance(obj, list):
            length = len(obj)
            if length > max_safe_items:
                raise LimitExceeded(f"List length {length} exceeds max_safe_items ({max_safe_items})")
            max_found = max(max_found, length)

            for item in obj:
                if isinstance(item, (dict, list)):
                    stack.append(item)

        elif isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)

    return max_found


def check_payload_limits(
    payload: Any,
    max_bytes: int,
    max_depth_limit: int,
    max_list_limit: int,
) -> None:
    """Enforce all payload limits. Raises LimitExceeded if any violated.

    Args:
        payload: payload to check
        max_bytes: max canonical JSON bytes
        max_depth_limit: max nesting depth
        max_list_limit: max items in any list

    Raises:
        TypeError: if payload is not JSON-serializable
        LimitExceeded: if any limit is violated
    """
    # Check JSON serializability and byte size
    byte_size = canonical_json_bytes(payload)
    if byte_size > max_bytes:
        raise LimitExceeded(f"Payload size {byte_size} exceeds max_bytes ({max_bytes})")

    # Check depth
    depth = max_depth(payload, max_safe_depth=max_depth_limit + 10)
    if depth > max_depth_limit:
        raise LimitExceeded(f"Payload depth {depth} exceeds max_depth ({max_depth_limit})")

    # Check list items
    list_items = max_list_items(payload, max_safe_items=max_list_limit + 100)
    if list_items > max_list_limit:
        raise LimitExceeded(f"Max list items {list_items} exceeds max_list_items ({max_list_limit})")
