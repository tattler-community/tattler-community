"""Validate notification context dicts against context.json declarations.

Provides :func:`assert_context_complete` for use in unittest test cases to verify
that the context passed to ``send_notification()`` covers all keys and types
declared in the corresponding ``context.json`` template file.
"""

from __future__ import annotations
import json
import os
import unittest
from typing import Any, Optional
from collections.abc import Mapping
from pathlib import Path

from tattler.utils.serialization import serialize_json, deserialize_json


def load_expected_context(templates_base: str | os.PathLike,
                          scope: str, event: str) -> dict[str, Any]:
    """Load and deserialize context.json for a given scope/event.

    :param templates_base: Path to the templates root directory.
    :param scope: Notification scope (e.g. ``'lab_sync'``).
    :param event: Event name (e.g. ``'order_committed'``).
    :raises FileNotFoundError: If context.json does not exist.
    :return: Deserialized context dict with real Python types.
    """
    path = Path(templates_base) / scope / event / 'context.json'
    return deserialize_json(path.read_bytes())


def _type_name(value: Any) -> str:
    """Return a readable type name for error messages."""
    return type(value).__name__


def _validate_recursive(expected: Any, actual: Any, path: str,
                        errors: list[str], accept_null: bool = True) -> None:
    """Recursively validate that actual covers the structure of expected.

    :param expected: The expected value from deserialized context.json.
    :param actual: The actual value from the serialized+deserialized context.
    :param path: Dotted path for error messages (e.g. ``'order.appointment'``).
    :param errors: Accumulator list for error messages.
    :param accept_null: If True (default), allow None for any field.
    """
    if expected is None:
        return
    if actual is None:
        if not accept_null:
            errors.append(f"'{path}': expected {_type_name(expected)}, got None")
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            errors.append(f"'{path}': expected dict, got {_type_name(actual)}")
            return
        for key in expected:
            if key not in actual:
                errors.append(f"'{path}.{key}': missing key")
                continue
            _validate_recursive(expected[key], actual[key], f'{path}.{key}', errors, accept_null)
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            errors.append(f"'{path}': expected list, got {_type_name(actual)}")
            return
        if expected and isinstance(expected[0], dict) and actual:
            for i, item in enumerate(actual):
                _validate_recursive(expected[0], item, f'{path}[{i}]', errors, accept_null)
    else:
        if not isinstance(actual, type(expected)):
            errors.append(f"'{path}': expected {_type_name(expected)}, got {_type_name(actual)}")


def assert_context_complete(test_case: unittest.TestCase,
                            scope: str, event: str,
                            context: Mapping[str, Any],
                            templates_base: str | os.PathLike,
                            accept_null: bool = True) -> None:
    """Assert that *context* covers all keys and types from context.json.

    First serializes *context* via :func:`serialize_json` (asserting
    serializability), then deserializes both sides and compares structure.

    :param test_case: The :class:`unittest.TestCase` instance (for assertions).
    :param scope: Notification scope (e.g. ``'website'``).
    :param event: Event name (e.g. ``'order_confirmation'``).
    :param context: The context dict passed to ``send_notification()``.
    :param templates_base: Path to the templates root directory.
    :param accept_null: If True (default), allow None for any field.
    :raises AssertionError: If context is not serializable or misses keys/types.
    """
    # Step 1: assert serializability and normalize
    try:
        serialized = serialize_json(context)
    except (TypeError, ValueError) as e:
        test_case.fail(f"{scope}/{event}: context is not serializable: {e}")
    actual = deserialize_json(serialized)
    # Step 2: load expected structure
    expected = load_expected_context(templates_base, scope, event)
    if not expected:
        return
    # Step 3: recursive validation
    errors: list[str] = []
    _validate_recursive(expected, actual, '', errors, accept_null)
    if errors:
        detail = '\n  '.join(errors)
        test_case.fail(f"{scope}/{event}: context validation failed:\n  {detail}")
