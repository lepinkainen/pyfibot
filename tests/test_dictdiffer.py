# -*- coding: utf-8 -*-
import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyfibot.util.dictdiffer import DictDiffer


class TestDictDiffer:
    """Test the DictDiffer utility class"""

    def test_empty_dicts(self):
        """Test with empty dictionaries"""
        differ = DictDiffer({}, {})
        assert differ.added() == set()
        assert differ.removed() == set()
        assert differ.changed() == set()
        assert differ.unchanged() == set()

    def test_identical_dicts(self):
        """Test with identical dictionaries"""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"a": 1, "b": 2, "c": 3}
        differ = DictDiffer(dict1, dict2)
        
        assert differ.added() == set()
        assert differ.removed() == set()
        assert differ.changed() == set()
        assert differ.unchanged() == {"a", "b", "c"}

    def test_added_keys(self):
        """Test detection of added keys"""
        past_dict = {"a": 1, "b": 2}
        current_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == {"c", "d"}
        assert differ.removed() == set()
        assert differ.changed() == set()
        assert differ.unchanged() == {"a", "b"}

    def test_removed_keys(self):
        """Test detection of removed keys"""
        past_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        current_dict = {"a": 1, "b": 2}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == set()
        assert differ.removed() == {"c", "d"}
        assert differ.changed() == set()
        assert differ.unchanged() == {"a", "b"}

    def test_changed_values(self):
        """Test detection of changed values"""
        past_dict = {"a": 1, "b": 2, "c": 3}
        current_dict = {"a": 10, "b": 2, "c": 30}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == set()
        assert differ.removed() == set()
        assert differ.changed() == {"a", "c"}
        assert differ.unchanged() == {"b"}

    def test_complex_scenario(self):
        """Test a complex scenario with all types of changes"""
        past_dict = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        current_dict = {"a": 10, "b": 2, "f": 6, "g": 7}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == {"f", "g"}
        assert differ.removed() == {"c", "d", "e"}
        assert differ.changed() == {"a"}
        assert differ.unchanged() == {"b"}

    def test_different_value_types(self):
        """Test with different value types"""
        past_dict = {"str": "hello", "int": 42, "list": [1, 2, 3], "none": None}
        current_dict = {"str": "world", "int": 42, "list": [1, 2, 4], "bool": True}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == {"bool"}
        assert differ.removed() == {"none"}
        assert differ.changed() == {"str", "list"}
        assert differ.unchanged() == {"int"}

    def test_nested_dicts(self):
        """Test with nested dictionaries"""
        past_dict = {"nested": {"a": 1, "b": 2}, "simple": "value"}
        current_dict = {"nested": {"a": 1, "b": 3}, "simple": "value"}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == set()
        assert differ.removed() == set()
        assert differ.changed() == {"nested"}  # The nested dict changed
        assert differ.unchanged() == {"simple"}

    def test_mixed_key_types(self):
        """Test with mixed key types (strings, integers, tuples)"""
        past_dict = {"str_key": 1, 42: "int_key", (1, 2): "tuple_key"}
        current_dict = {"str_key": 2, 42: "int_key", (3, 4): "new_tuple"}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == {(3, 4)}
        assert differ.removed() == {(1, 2)}
        assert differ.changed() == {"str_key"}
        assert differ.unchanged() == {42}

    def test_none_values(self):
        """Test handling of None values"""
        past_dict = {"a": None, "b": 1, "c": None}
        current_dict = {"a": 1, "b": None, "c": None}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == set()
        assert differ.removed() == set()
        assert differ.changed() == {"a", "b"}
        assert differ.unchanged() == {"c"}

    def test_large_dicts(self):
        """Test performance with larger dictionaries"""
        past_dict = {f"key_{i}": i for i in range(1000)}
        current_dict = {f"key_{i}": i * 2 for i in range(500, 1500)}
        differ = DictDiffer(current_dict, past_dict)
        
        added = differ.added()
        removed = differ.removed()
        changed = differ.changed()
        unchanged = differ.unchanged()
        
        # Keys 0-499 were removed
        assert len(removed) == 500
        # Keys 1000-1499 were added
        assert len(added) == 500
        # Keys 500-999 had values changed (i vs i*2)
        assert len(changed) == 500
        # No keys should be unchanged since all overlapping keys had value changes
        assert len(unchanged) == 0

    def test_boolean_values(self):
        """Test with boolean values"""
        past_dict = {"flag1": True, "flag2": False, "flag3": True}
        current_dict = {"flag1": False, "flag2": False, "flag4": True}
        differ = DictDiffer(current_dict, past_dict)
        
        assert differ.added() == {"flag4"}
        assert differ.removed() == {"flag3"}
        assert differ.changed() == {"flag1"}
        assert differ.unchanged() == {"flag2"}