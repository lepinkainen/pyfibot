# -*- coding: utf-8 -*-
import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import from pyfibot module directly
from pyfibot import pyfibot


class TestUtilityFunctions:
    """Test utility functions from PyFiBotFactory"""

    def setup_method(self):
        """Setup test fixtures"""
        # Create a minimal config for testing
        config = {"admins": ["admin@example.com", "*@admin.domain"]}
        self.factory = pyfibot.PyFiBotFactory(config)

    def test_to_utf8_string_input(self):
        """Test to_utf8 with string input"""
        result = self.factory.to_utf8("hello world")
        assert result == b"hello world"
        assert isinstance(result, bytes)

    def test_to_utf8_unicode_string(self):
        """Test to_utf8 with unicode characters"""
        result = self.factory.to_utf8("héllo wörld åäö")
        expected = "héllo wörld åäö".encode("UTF-8")
        assert result == expected
        assert isinstance(result, bytes)

    def test_to_utf8_bytes_input(self):
        """Test to_utf8 with bytes input (should return as-is)"""
        input_bytes = b"hello world"
        result = self.factory.to_utf8(input_bytes)
        assert result == input_bytes
        assert isinstance(result, bytes)

    def test_to_utf8_none_input(self):
        """Test to_utf8 with None input"""
        result = self.factory.to_utf8(None)
        assert result is None

    def test_to_utf8_numeric_input(self):
        """Test to_utf8 with numeric input"""
        result = self.factory.to_utf8(42)
        assert result == 42
        assert not isinstance(result, bytes)

    def test_to_unicode_bytes_input_utf8(self):
        """Test to_unicode with UTF-8 bytes"""
        input_bytes = "héllo wörld".encode("utf-8")
        result = self.factory.to_unicode(input_bytes)
        assert result == "héllo wörld"
        assert isinstance(result, str)

    def test_to_unicode_bytes_input_iso88591(self):
        """Test to_unicode with ISO-8859-1 bytes that fail UTF-8 decode"""
        # Create bytes that are valid ISO-8859-1 but invalid UTF-8
        input_bytes = b"\xe5\xe4\xf6"  # åäö in ISO-8859-1
        result = self.factory.to_unicode(input_bytes)
        assert result == "åäö"
        assert isinstance(result, str)

    def test_to_unicode_invalid_bytes(self):
        """Test to_unicode with bytes that can't be decoded as UTF-8 or ISO-8859-1"""
        # This shouldn't happen in practice, but test the fallback
        input_bytes = b"\xff\xfe\x00\x00"
        result = self.factory.to_unicode(input_bytes)
        assert isinstance(result, str)
        # Should fall back to str() conversion

    def test_to_unicode_string_input(self):
        """Test to_unicode with string input (should return as-is)"""
        input_str = "hello world"
        result = self.factory.to_unicode(input_str)
        assert result == input_str
        assert isinstance(result, str)

    def test_to_unicode_none_input(self):
        """Test to_unicode with None input"""
        result = self.factory.to_unicode(None)
        assert result == "None"
        assert isinstance(result, str)

    def test_to_unicode_numeric_input(self):
        """Test to_unicode with numeric input"""
        result = self.factory.to_unicode(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_to_unicode_list_input(self):
        """Test to_unicode with list input"""
        result = self.factory.to_unicode([1, 2, 3])
        assert result == "[1, 2, 3]"
        assert isinstance(result, str)

    def test_roundtrip_conversion(self):
        """Test that to_utf8 and to_unicode are inverse operations"""
        original = "héllo wörld åäö"
        bytes_result = self.factory.to_utf8(original)
        string_result = self.factory.to_unicode(bytes_result)
        assert string_result == original

    def test_empty_string_conversion(self):
        """Test conversion of empty strings"""
        assert self.factory.to_utf8("") == b""
        assert self.factory.to_unicode(b"") == ""

    def test_special_characters(self):
        """Test with various special characters"""
        test_strings = [
            "🙂😀💯",  # Emojis
            "中文字符",  # Chinese characters
            "русский текст",  # Cyrillic
            "العربية",  # Arabic
            "→←↑↓",  # Arrows
            "¡¿¨´`",  # Special punctuation
        ]
        
        for test_str in test_strings:
            # Test roundtrip
            bytes_result = self.factory.to_utf8(test_str)
            string_result = self.factory.to_unicode(bytes_result)
            assert string_result == test_str


class TestAdminCheck:
    """Test the isAdmin functionality"""

    def test_exact_match_admin(self):
        """Test exact admin match"""
        config = {"admins": ["admin@example.com"]}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.isAdmin("admin@example.com") is True
        assert factory.isAdmin("user@example.com") is False

    def test_wildcard_admin(self):
        """Test wildcard admin patterns"""
        config = {"admins": ["*@admin.domain", "admin@*"]}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.isAdmin("anyone@admin.domain") is True
        assert factory.isAdmin("admin@anywhere.com") is True
        assert factory.isAdmin("user@regular.domain") is False

    def test_multiple_admin_patterns(self):
        """Test multiple admin patterns"""
        config = {"admins": ["admin1@test.com", "*@secure.net", "root@*"]}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.isAdmin("admin1@test.com") is True
        assert factory.isAdmin("user@secure.net") is True
        assert factory.isAdmin("root@anywhere.org") is True
        assert factory.isAdmin("user@test.com") is False

    def test_no_admins_configured(self):
        """Test when no admins are configured"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.isAdmin("anyone@anywhere.com") is False

    def test_complex_wildcard_patterns(self):
        """Test complex wildcard patterns"""
        config = {"admins": ["admin*@*.example.com", "*admin@test.*"]}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.isAdmin("admin123@sub.example.com") is True
        assert factory.isAdmin("superadmin@test.org") is True
        assert factory.isAdmin("user@sub.example.com") is False
        assert factory.isAdmin("admin@wrongdomain.com") is False

    def test_case_sensitivity(self):
        """Test case sensitivity in admin matching"""
        config = {"admins": ["Admin@Example.Com"]}
        factory = pyfibot.PyFiBotFactory(config)
        
        # fnmatch is case-sensitive by default
        assert factory.isAdmin("Admin@Example.Com") is True
        assert factory.isAdmin("admin@example.com") is False


class TestHostnameExtraction:
    """Test hostname extraction utilities"""

    def test_getHost_basic(self):
        """Test basic hostname extraction"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.getHost("user@example.com") == "example.com"
        assert factory.getHost("nick@host.domain.org") == "host.domain.org"

    def test_getHost_no_at_symbol(self):
        """Test hostname extraction with no @ symbol"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        # Should return the whole string if no @ found
        result = factory.getHost("justnick")
        # This will split on @ and take [1], which doesn't exist, so it might error
        # Let's check what actually happens
        with pytest.raises(IndexError):
            factory.getHost("justnick")

    def test_getHost_multiple_at_symbols(self):
        """Test hostname extraction with multiple @ symbols"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        # Should split on first @ and take everything after
        assert factory.getHost("user@with@multiple@ats") == "with@multiple@ats"

    def test_getIdent_basic(self):
        """Test basic ident extraction"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        assert factory.getIdent("nick!ident@host.com") == "ident"
        assert factory.getIdent("user!~username@example.org") == "~username"

    def test_getIdent_no_exclamation(self):
        """Test ident extraction with no ! symbol"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        # Should return the whole string if no ! found
        with pytest.raises(IndexError):
            factory.getIdent("nickonly")

    def test_getIdent_complex_format(self):
        """Test ident extraction with complex IRC format"""
        config = {"admins": []}
        factory = pyfibot.PyFiBotFactory(config)
        
        # Test various IRC user formats
        assert factory.getIdent("nick!ident@host") == "ident"
        assert factory.getIdent("user!~ident@cloak.host.net") == "~ident"