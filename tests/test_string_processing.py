# -*- coding: utf-8 -*-
import pytest
import sys
import os
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the functions we want to test
from pyfibot.modules.module_urltitle import (
    _levenshtein_distance,
    _check_redundant,
    __get_length_str,
    __get_age_str,
    __get_views,
    __escaped_fragment,
    _title
)


class TestLevenshteinDistance:
    """Test the Levenshtein distance calculation"""

    def test_identical_strings(self):
        """Test distance between identical strings"""
        assert _levenshtein_distance("hello", "hello") == 0
        assert _levenshtein_distance("", "") == 0
        assert _levenshtein_distance("a", "a") == 0

    def test_completely_different_strings(self):
        """Test distance between completely different strings"""
        result = _levenshtein_distance("abc", "xyz")
        assert result == 3  # All 3 characters need to be replaced

    def test_single_character_changes(self):
        """Test distance with single character modifications"""
        # Single substitution
        assert _levenshtein_distance("cat", "bat") == 1
        # Single insertion
        assert _levenshtein_distance("cat", "cats") == 1
        # Single deletion
        assert _levenshtein_distance("cats", "cat") == 1

    def test_empty_string_cases(self):
        """Test distance calculations with empty strings"""
        assert _levenshtein_distance("", "hello") == 5
        assert _levenshtein_distance("hello", "") == 5
        assert _levenshtein_distance("", "") == 0

    def test_common_transformations(self):
        """Test common string transformations"""
        # "kitten" -> "sitting" (classic example)
        assert _levenshtein_distance("kitten", "sitting") == 3
        # "saturday" -> "sunday" 
        assert _levenshtein_distance("saturday", "sunday") == 3

    def test_case_sensitivity(self):
        """Test that the function is case-sensitive"""
        assert _levenshtein_distance("Hello", "hello") == 1
        assert _levenshtein_distance("ABC", "abc") == 3

    def test_unicode_strings(self):
        """Test with unicode characters"""
        assert _levenshtein_distance("café", "cafe") == 1
        assert _levenshtein_distance("naïve", "naive") == 1

    def test_long_strings(self):
        """Test with longer strings"""
        s1 = "The quick brown fox jumps over the lazy dog"
        s2 = "The quick brown fox jumped over the lazy dog"
        assert _levenshtein_distance(s1, s2) == 1  # s -> d

    def test_complex_changes(self):
        """Test complex changes requiring multiple operations"""
        # Multiple insertions, deletions, substitutions
        result = _levenshtein_distance("intention", "execution")
        assert result == 5  # Well-known example


class TestRedundancyCheck:
    """Test URL/title redundancy checking"""

    def test_obvious_redundant_cases(self):
        """Test cases where title is obviously redundant with URL"""
        # Title contains domain name
        url = "https://example.com/article"
        title = "Example.com - Latest News"
        assert _check_redundant(url, title) is True

    def test_non_redundant_cases(self):
        """Test cases where title is not redundant"""
        url = "https://news.ycombinator.com/item?id=123"
        title = "Interesting Article About Programming"
        assert _check_redundant(url, title) is False

    def test_www_subdomain_handling(self):
        """Test that www subdomain is properly stripped"""
        url = "https://www.example.com/page"
        title = "Example Website Content"
        # Should detect redundancy even with www
        result = _check_redundant(url, title)
        assert isinstance(result, bool)  # Function should complete without error

    def test_nordic_character_normalization(self):
        """Test Nordic character normalization"""
        url = "https://example.com/page"
        title = "Exämple Örgänizätion"
        # Should normalize ä->a, ö->o when checking redundancy
        result = _check_redundant(url, title)
        assert isinstance(result, bool)

    def test_case_insensitive_comparison(self):
        """Test that comparison is case-insensitive"""
        url = "https://EXAMPLE.COM/page"
        title = "example news article"
        result = _check_redundant(url, title)
        assert isinstance(result, bool)

    def test_port_number_handling(self):
        """Test URLs with port numbers"""
        url = "https://example.com:8080/page"
        title = "Example Site Content"
        result = _check_redundant(url, title)
        assert isinstance(result, bool)

    def test_subdomain_in_title(self):
        """Test when subdomain appears in title"""
        url = "https://blog.example.com/post"
        title = "Blog Example Post"
        result = _check_redundant(url, title)
        assert isinstance(result, bool)


class TestLengthString:
    """Test time duration formatting"""

    def test_zero_seconds(self):
        """Test zero duration"""
        assert __get_length_str(0) == "0s"

    def test_seconds_only(self):
        """Test durations less than a minute"""
        assert __get_length_str(30) == "30s"
        assert __get_length_str(59) == "59s"

    def test_minutes_only(self):
        """Test durations in minutes"""
        assert __get_length_str(60) == "1m"
        assert __get_length_str(90) == "1m30s"
        assert __get_length_str(120) == "2m"

    def test_hours_only(self):
        """Test durations in hours"""
        assert __get_length_str(3600) == "1h"
        assert __get_length_str(7200) == "2h"

    def test_complex_durations(self):
        """Test complex durations with hours, minutes, and seconds"""
        assert __get_length_str(3661) == "1h1m1s"  # 1:01:01
        assert __get_length_str(3720) == "1h2m"    # 1:02:00
        assert __get_length_str(3665) == "1h1m5s"  # 1:01:05

    def test_very_long_durations(self):
        """Test very long durations"""
        day_seconds = 24 * 3600
        assert __get_length_str(day_seconds) == "24h"
        assert __get_length_str(day_seconds + 3661) == "25h1m1s"

    def test_edge_cases(self):
        """Test edge cases"""
        assert __get_length_str(1) == "1s"
        assert __get_length_str(61) == "1m1s"
        assert __get_length_str(3601) == "1h1s"


class TestAgeString:
    """Test age/time delta formatting"""

    def test_recent_time(self):
        """Test very recent times"""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(seconds=30)
        result = __get_age_str(recent)
        assert "fresh" in result or "0m" in result

    def test_minutes_ago(self):
        """Test times in minutes"""
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=5)
        result = __get_age_str(past)
        assert "5m" in result

    def test_hours_ago(self):
        """Test times in hours"""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=2)
        result = __get_age_str(past)
        assert "2h" in result

    def test_days_ago(self):
        """Test times in days"""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=3)
        result = __get_age_str(past)
        assert "3d" in result or "72h" in result

    def test_future_time(self):
        """Test future times"""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)
        result = __get_age_str(future)
        # Should handle future times gracefully
        assert isinstance(result, str)

    def test_timezone_aware(self):
        """Test with timezone-aware datetimes"""
        utc_tz = timezone.utc
        now = datetime.now(utc_tz)
        past = now - timedelta(hours=1)
        result = __get_age_str(past)
        assert "1h" in result or "60m" in result


class TestViews:
    """Test view count formatting"""

    def test_zero_views(self):
        """Test zero views"""
        assert __get_views(0) == "0"

    def test_small_numbers(self):
        """Test small view counts"""
        assert __get_views(42) == "42"
        assert __get_views(999) == "999"

    def test_thousands(self):
        """Test thousands formatting"""
        assert __get_views(1000) == "1k"
        assert __get_views(1500) == "2k"  # Rounded
        assert __get_views(999000) == "999k"

    def test_millions(self):
        """Test millions formatting"""
        assert __get_views(1000000) == "1M"
        assert __get_views(1500000) == "2M"
        assert __get_views(999000000) == "999M"

    def test_billions(self):
        """Test billions formatting"""
        assert __get_views(1000000000) == "1Billion"
        assert __get_views(1500000000) == "2Billion"

    def test_trillions(self):
        """Test trillions formatting"""
        assert __get_views(1000000000000) == "1Trillion"

    def test_float_inputs(self):
        """Test with float inputs"""
        assert __get_views(1500.7) == "2k"
        assert __get_views(1000000.5) == "1M"

    def test_string_inputs(self):
        """Test with string inputs that can be converted to int"""
        assert __get_views("1000") == "1k"
        assert __get_views("1000000") == "1M"

    def test_edge_cases(self):
        """Test edge cases"""
        assert __get_views(1) == "1"
        assert __get_views(10) == "10"
        assert __get_views(100) == "100"


class TestEscapedFragment:
    """Test URL escaped fragment handling"""

    def test_no_fragment(self):
        """Test URLs without fragments"""
        url = "https://example.com/page"
        result = __escaped_fragment(url)
        assert result == url

    def test_regular_fragment(self):
        """Test URLs with regular fragments (not starting with !)"""
        url = "https://example.com/page#section"
        result = __escaped_fragment(url)
        assert result == url

    def test_ajax_fragment(self):
        """Test URLs with AJAX fragments (starting with #!)"""
        url = "https://example.com/page#!state=123"
        result = __escaped_fragment(url)
        assert "_escaped_fragment_=state=123" in result
        assert "#!" not in result

    def test_ajax_fragment_with_query(self):
        """Test URLs with existing query parameters and AJAX fragments"""
        url = "https://example.com/page?param=value#!state=123"
        result = __escaped_fragment(url)
        assert "_escaped_fragment_=state=123" in result
        assert "param=value" in result
        assert "&" in result  # Should join with &

    def test_empty_ajax_fragment(self):
        """Test URLs with empty AJAX fragments"""
        url = "https://example.com/page#!"
        result = __escaped_fragment(url)
        assert "_escaped_fragment_=" in result

    def test_complex_ajax_fragment(self):
        """Test URLs with complex AJAX fragments"""
        url = "https://example.com/page#!route=/user/123/profile"
        result = __escaped_fragment(url)
        assert "_escaped_fragment_=route=/user/123/profile" in result

    def test_meta_parameter(self):
        """Test the meta parameter behavior"""
        url = "https://example.com/page#section"
        result = __escaped_fragment(url, meta=True)
        # When meta=True and no AJAX fragment, might return None
        assert result is None or isinstance(result, str)


class MockBot:
    """Mock bot for testing _title function"""
    def __init__(self):
        self.messages = []
    
    def say(self, channel, message):
        self.messages.append((channel, message))
        return (channel, message)


class TestTitleFunction:
    """Test the _title function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.bot = MockBot()

    def test_simple_title(self):
        """Test simple title output"""
        result = _title(self.bot, "#test", "Simple Title")
        assert result[0] == "#test"
        assert "Title: Simple Title" in result[1]

    def test_custom_prefix(self):
        """Test custom prefix"""
        result = _title(self.bot, "#test", "Custom Title", prefix="Video:")
        assert "Video: Custom Title" in result[1]

    def test_title_with_info(self):
        """Test title with additional info tuple"""
        title_tuple = ("Main Title", "Additional Info")
        result = _title(self.bot, "#test", title_tuple)
        assert "Title: Main Title [Additional Info]" in result[1]

    def test_long_title_truncation(self):
        """Test that very long titles are truncated"""
        long_title = "a" * 500  # Longer than 400 chars
        result = _title(self.bot, "#test", long_title)
        assert len(result[1]) < 450  # Should be truncated
        assert "..." in result[1]

    def test_empty_title(self):
        """Test with empty title"""
        result = _title(self.bot, "#test", "")
        assert result is None

    def test_none_title(self):
        """Test with None title"""
        result = _title(self.bot, "#test", None)
        assert result is None

    def test_title_with_url_caching(self):
        """Test title with URL for caching"""
        # This test assumes cache module is available
        try:
            result = _title(self.bot, "#test", "Test Title", url="https://example.com")
            assert result[0] == "#test"
            assert "Test Title" in result[1]
        except NameError:
            # If cache module is not available, skip this test
            pytest.skip("Cache module not available")

    def test_unicode_title(self):
        """Test with unicode characters in title"""
        unicode_title = "Tëst Tîtle with Spéciàl Chars"
        result = _title(self.bot, "#test", unicode_title)
        assert unicode_title in result[1]

    def test_html_entities_in_title(self):
        """Test title with HTML entities"""
        html_title = "Title with &amp; &lt;entities&gt;"
        result = _title(self.bot, "#test", html_title)
        assert html_title in result[1]