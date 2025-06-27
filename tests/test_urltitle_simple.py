# -*- coding: utf-8 -*-
"""
Simple unit tests for URL title handler functionality.
Tests key functions without requiring full bot setup.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from pyfibot.modules import module_urltitle


def test_get_length_str():
    """Test conversion of seconds to human readable format"""
    # Access the private function directly
    get_length_str = module_urltitle.__get_length_str

    assert get_length_str(0) == "0s"
    assert get_length_str(30) == "30s"
    assert get_length_str(60) == "1m"
    assert get_length_str(90) == "1m30s"
    assert get_length_str(3600) == "1h"
    assert get_length_str(3661) == "1h1m1s"
    assert get_length_str(7200) == "2h"


def test_get_views():
    """Test conversion of view counts to human readable format"""
    get_views = module_urltitle.__get_views

    assert get_views(0) == "0"
    assert get_views(500) == "500"
    assert get_views(1500) == "2k"
    assert get_views(1000000) == "1M"
    assert get_views(1500000000) == "2Billion"


def test_levenshtein_distance():
    """Test Levenshtein distance calculation"""
    distance = module_urltitle._levenshtein_distance

    assert distance("", "") == 0
    assert distance("a", "") == 1
    assert distance("", "a") == 1
    assert distance("abc", "abc") == 0
    assert distance("abc", "ab") == 1
    assert distance("abc", "def") == 3
    assert distance("kitten", "sitting") == 3


def test_escaped_fragment():
    """Test Google escaped fragment URL transformation"""
    escaped_fragment = module_urltitle.__escaped_fragment

    # URL without fragment
    url1 = "http://example.com/page"
    assert escaped_fragment(url1) == url1

    # URL with hash-bang fragment
    url2 = "http://example.com/page#!/content"
    expected2 = "http://example.com/page?_escaped_fragment_=/content"
    assert escaped_fragment(url2) == expected2

    # URL with query and fragment
    url3 = "http://example.com/page?param=value#!/content"
    expected3 = "http://example.com/page?param=value&_escaped_fragment_=/content"
    assert escaped_fragment(url3) == expected3


def test_check_redundant():
    """Test redundant URL/title detection"""
    check_redundant = module_urltitle._check_redundant

    # Very similar URL and title should be redundant
    url1 = "http://example.com/test-page-name"
    title1 = "Test Page Name"
    assert check_redundant(url1, title1) == True

    # Different URL and title should not be redundant
    url2 = "http://example.com/xyz123"
    title2 = "Completely Different Article About Something Else"
    assert check_redundant(url2, title2) == False

    # Short titles with similar content should be redundant
    url3 = "http://test.com/abc"
    title3 = "abc"
    assert check_redundant(url3, title3) == True


class TestUrlTitleCoreLogic:
    """Test core URL title extraction logic"""

    def create_mock_bot(self):
        """Create a minimal mock bot for testing"""
        bot = Mock()
        bot.config = {"module_urltitle": {}}
        return bot

    def test_title_function_basic(self):
        """Test the _title function that formats and outputs titles"""
        bot = self.create_mock_bot()
        bot.say.return_value = ("channel", "message")

        # Test basic title output
        result = module_urltitle._title(bot, "#test", "Test Title")
        bot.say.assert_called_with("#test", "Title: Test Title")

        # Test title with custom prefix
        result = module_urltitle._title(bot, "#test", "Test Title", prefix="Custom:")
        bot.say.assert_called_with("#test", "Custom: Test Title")

    def test_title_function_with_info(self):
        """Test the _title function with additional info tuple"""
        bot = self.create_mock_bot()
        bot.say.return_value = ("channel", "message")

        # Test title with additional info
        title_tuple = ("Test Title", "Extra Info")
        result = module_urltitle._title(bot, "#test", title_tuple)
        bot.say.assert_called_with("#test", "Title: Test Title [Extra Info]")

    def test_title_function_long_title(self):
        """Test title truncation for very long titles"""
        bot = self.create_mock_bot()
        bot.say.return_value = ("channel", "message")

        # Test very long title gets truncated
        long_title = "A" * 500
        result = module_urltitle._title(bot, "#test", long_title)

        # Should be called with truncated title
        call_args = bot.say.call_args[0][1]
        assert len(call_args) <= 410  # "Title: " + 400 chars + "..."
        assert call_args.endswith("...")

    def test_title_function_caching(self):
        """Test that titles are cached when URL is provided"""
        bot = self.create_mock_bot()
        bot.say.return_value = ("channel", "message")

        # Clear any existing cache
        module_urltitle.cache.clear()

        url = "http://example.com/test"
        title = "Test Title"

        # Call with URL should cache the result
        result = module_urltitle._title(bot, "#test", title, url=url)

        # Check that title was cached
        cached_title = module_urltitle.cache.get(url)
        assert cached_title == title


class TestUrlTitleEndToEnd:
    """End-to-end tests with minimal mocking"""

    def setup_method(self):
        """Set up test environment"""
        # Create minimal bot mock
        self.bot = Mock()
        self.bot.config = {"module_urltitle": {}}
        self.bot.say.return_value = ("#channel", "message")

        # Initialize module
        module_urltitle.init(self.bot)

    def test_handle_url_invalid_inputs(self):
        """Test handle_url with invalid inputs"""
        # None URL
        result = module_urltitle.handle_url(
            self.bot, "user", "#channel", None, "message"
        )
        assert result is None

        # Non-string URL
        result = module_urltitle.handle_url(
            self.bot, "user", "#channel", 123, "message"
        )
        assert result is None

        # Empty URL
        result = module_urltitle.handle_url(self.bot, "user", "#channel", "", "message")
        assert result is None

    def test_handle_url_manual_ignore(self):
        """Test handle_url with manual ignore prefix"""
        url = "http://example.com"
        msg = "- " + url

        result = module_urltitle.handle_url(self.bot, "user", "#channel", url, msg)
        assert result is None

    def test_handle_url_spotify_ignore(self):
        """Test that Spotify URLs are ignored"""
        spotify_urls = [
            "https://open.spotify.com/track/123",
            "https://open.spotify.com/album/456",
            "spotify:track:789",
        ]

        for url in spotify_urls:
            result = module_urltitle.handle_url(self.bot, "user", "#channel", url, url)
            assert result is None
