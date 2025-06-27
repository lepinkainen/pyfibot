# -*- coding: utf-8 -*-
"""
A dictionary difference calculator
Originally posted as:
http://stackoverflow.com/questions/1165352/fast-comparison-between-two-python-dictionary/1165552#1165552
copied from https://github.com/hughdbrown/dictdiffer
"""

from typing import Dict, Set, Any


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict: Dict[Any, Any], past_dict: Dict[Any, Any]) -> None:
        self.current_dict = current_dict
        self.past_dict = past_dict
        self.current_keys: Set[Any] = set(current_dict.keys())
        self.past_keys: Set[Any] = set(past_dict.keys())
        self.intersect: Set[Any] = self.current_keys.intersection(self.past_keys)

    def added(self) -> Set[Any]:
        return self.current_keys - self.intersect

    def removed(self) -> Set[Any]:
        return self.past_keys - self.intersect

    def changed(self) -> Set[Any]:
        return set(
            o for o in self.intersect if self.past_dict[o] != self.current_dict[o]
        )

    def unchanged(self) -> Set[Any]:
        return set(
            o for o in self.intersect if self.past_dict[o] == self.current_dict[o]
        )
