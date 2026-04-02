"""Tests for tattler's context validation logic"""

import json
import os
import tempfile
import unittest
from datetime import datetime, date
from pathlib import Path
from types import SimpleNamespace

from tattler.utils import context_validation


def _mk_templates(tmpdir: str, scope: str, event: str,
                  context: dict) -> Path:
    """Create a temporary templates directory with a context.json file."""
    base = Path(tmpdir)
    event_dir = base / scope / event
    event_dir.mkdir(parents=True, exist_ok=True)
    ctx_path = event_dir / 'context.json'
    ctx_path.write_text(json.dumps(context))
    return base


class LoadExpectedContextTest(unittest.TestCase):
    """Tests for load_expected_context()"""

    def test_load_valid_context(self):
        """load_expected_context() loads and deserializes context.json"""
        want_ctx = {'order': {'number': 'abc123'}}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 'myscope', 'myevent', want_ctx)
            got = context_validation.load_expected_context(base, 'myscope', 'myevent')
            self.assertEqual(want_ctx, got)

    def test_load_context_deserializes_tattler_types(self):
        """load_expected_context() deserializes ^tattler^ markers into real types"""
        raw = {'appointment': '^tattler^datetime^2024-06-28T18:15:04'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', raw)
            got = context_validation.load_expected_context(base, 's', 'e')
            self.assertIsInstance(got['appointment'], datetime)

    def test_load_missing_context_raises(self):
        """load_expected_context() raises FileNotFoundError for missing context.json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                context_validation.load_expected_context(tmpdir, 'no', 'exist')


class AssertContextCompleteTest(unittest.TestCase):
    """Tests for assert_context_complete()"""

    def test_matching_flat_context_passes(self):
        """Flat context matching expected keys and types passes"""
        want_ctx = {'name': 'foo', 'count': 42}
        actual = {'name': 'bar', 'count': 7}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_missing_key_fails(self):
        """Missing top-level key causes assertion failure"""
        want_ctx = {'name': 'foo', 'count': 42}
        actual = {'name': 'bar'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('count', str(cm.exception))
            self.assertIn('missing key', str(cm.exception))

    def test_nested_dict_validated(self):
        """Nested dict keys are validated recursively"""
        want_ctx = {'order': {'number': 'abc', 'date': 'x'}}
        actual = {'order': {'number': 'def'}}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('order.date', str(cm.exception))

    def test_type_mismatch_fails(self):
        """Wrong value type causes assertion failure"""
        want_ctx = {'count': 42}
        actual = {'count': 'not_a_number'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('count', str(cm.exception))
            self.assertIn('int', str(cm.exception))

    def test_null_expected_accepts_any(self):
        """Null values in expected context accept any actual type"""
        want_ctx = {'ref': None}
        actual = {'ref': 'some_value'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_null_expected_accepts_null(self):
        """Null values in expected context accept null actual value"""
        want_ctx = {'ref': None}
        actual = {'ref': None}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_list_of_dicts_validated(self):
        """List of dicts has element keys validated against expected"""
        want_ctx = {'items': [{'name': 'x', 'value': 1}]}
        actual = {'items': [{'name': 'a'}, {'name': 'b'}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('value', str(cm.exception))
            self.assertIn('items[0]', str(cm.exception))

    def test_list_of_scalars_passes(self):
        """List of scalars only checks type is list, not element types"""
        want_ctx = {'prices': [100, 200]}
        actual = {'prices': [50]}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_expected_list_actual_not_list_fails(self):
        """Non-list actual where list expected causes failure"""
        want_ctx = {'items': [1, 2]}
        actual = {'items': 'not_a_list'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('list', str(cm.exception))

    def test_empty_expected_context_passes(self):
        """Empty expected context (no custom vars) passes any actual"""
        want_ctx = {}
        actual = {'anything': 'goes'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_not_serializable_fails(self):
        """Non-serializable context causes assertion failure"""
        want_ctx = {'name': 'foo'}
        actual = {'name': lambda: None}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('not serializable', str(cm.exception))

    def test_orm_object_serialized_to_dict(self):
        """ORM-like objects are serialized to dicts and validated"""
        want_ctx = {'order': {'number': 'abc', 'state': 'OPEN'}}
        order = SimpleNamespace(number='xyz', state='PAID', _internal='hidden')
        actual = {'order': order}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_datetime_type_validated(self):
        """Datetime fields from ^tattler^datetime^ markers are type-checked"""
        want_ctx = {'appointment': '^tattler^datetime^2024-06-28T18:15:04'}
        actual = {'appointment': datetime(2025, 1, 1)}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_datetime_type_mismatch_fails(self):
        """String where datetime expected causes failure"""
        want_ctx = {'appointment': '^tattler^datetime^2024-06-28T18:15:04'}
        actual = {'appointment': '2024-06-28'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            self.assertIn('datetime', str(cm.exception))

    def test_extra_keys_in_actual_accepted(self):
        """Extra keys in actual context beyond expected are fine"""
        want_ctx = {'name': 'foo'}
        actual = {'name': 'bar', 'extra': 'ignored'}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            context_validation.assert_context_complete(self, 's', 'e', actual, base)

    def test_multiple_errors_reported(self):
        """Multiple missing keys are all reported in one failure"""
        want_ctx = {'a': 'x', 'b': 'y', 'c': 'z'}
        actual = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            base = _mk_templates(tmpdir, 's', 'e', want_ctx)
            with self.assertRaises(AssertionError) as cm:
                context_validation.assert_context_complete(self, 's', 'e', actual, base)
            msg = str(cm.exception)
            self.assertIn("'.a'", msg)
            self.assertIn("'.b'", msg)
            self.assertIn("'.c'", msg)


if __name__ == '__main__':
    unittest.main()
