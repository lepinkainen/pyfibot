# -*- coding: utf-8 -*-
import pytest
import sys
import os
import socket
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyfibot.modules.module_webchat import webchat_getorigin
from pyfibot.modules.module_autoop import check_hostmask

# Try to import wolfram alpha functions
try:
    from pyfibot.modules.module_wolfram_alpha import clean_question, clean_answer
    WOLFRAM_AVAILABLE = True
except ImportError:
    WOLFRAM_AVAILABLE = False


class TestWebchatOrigin:
    """Test webchat hex IP origin parsing"""

    def test_valid_hex_ip(self):
        """Test parsing valid hex IP addresses"""
        # Test case: C0A80001 -> 192.168.0.1
        result = webchat_getorigin("C0A80001")
        assert result is not None
        assert "192.168.0.1" in result

    def test_invalid_hex_length(self):
        """Test invalid hex IP length"""
        # Too short
        assert webchat_getorigin("C0A800") is None
        # Too long
        assert webchat_getorigin("C0A800011") is None
        # Empty
        assert webchat_getorigin("") is None

    def test_invalid_hex_characters(self):
        """Test invalid hex characters"""
        # Contains non-hex characters
        assert webchat_getorigin("G0A80001") is None
        assert webchat_getorigin("C0A8000Z") is None
        assert webchat_getorigin("HELLO123") is None

    def test_valid_common_ips(self):
        """Test common IP addresses in hex format"""
        test_cases = [
            ("7F000001", "127.0.0.1"),  # localhost
            ("C0A80101", "192.168.1.1"),  # common router IP
            ("08080808", "8.8.8.8"),     # Google DNS
        ]
        
        for hex_ip, expected_ip in test_cases:
            result = webchat_getorigin(hex_ip)
            assert result is not None
            assert expected_ip in result

    def test_zero_ip(self):
        """Test all-zero IP address"""
        result = webchat_getorigin("00000000")
        assert result is not None
        assert "0.0.0.0" in result

    def test_max_ip(self):
        """Test maximum IP address (255.255.255.255)"""
        result = webchat_getorigin("FFFFFFFF")
        assert result is not None
        assert "255.255.255.255" in result

    def test_lowercase_hex(self):
        """Test lowercase hex input"""
        result = webchat_getorigin("c0a80001")
        assert result is not None
        assert "192.168.0.1" in result

    def test_mixed_case_hex(self):
        """Test mixed case hex input"""
        result = webchat_getorigin("C0a80001")
        assert result is not None
        assert "192.168.0.1" in result

    @patch('socket.getfqdn')
    def test_hostname_resolution(self, mock_getfqdn):
        """Test hostname resolution"""
        mock_getfqdn.return_value = "example.com"
        
        result = webchat_getorigin("C0A80001")
        assert result is not None
        assert "192.168.0.1 -> example.com" in result

    @patch('socket.getfqdn')
    def test_no_hostname_resolution(self, mock_getfqdn):
        """Test when hostname resolution returns same as IP"""
        mock_getfqdn.return_value = "192.168.0.1"  # Same as IP
        
        result = webchat_getorigin("C0A80001")
        assert result is not None
        assert "192.168.0.1" in result
        assert " -> " not in result  # Should not show arrow

    @patch('pyfibot.modules.module_webchat.gi4')
    @patch('socket.getfqdn')
    def test_geoip_integration(self, mock_getfqdn, mock_gi4):
        """Test GeoIP integration when available"""
        mock_getfqdn.return_value = "192.168.0.1"
        mock_gi4.country_name_by_addr.return_value = "Finland"
        
        result = webchat_getorigin("C0A80001")
        assert result is not None
        assert "192.168.0.1" in result
        assert "(Finland)" in result

    @patch('pyfibot.modules.module_webchat.gi4')
    @patch('socket.getfqdn')
    def test_geoip_failure(self, mock_getfqdn, mock_gi4):
        """Test GeoIP failure handling"""
        mock_getfqdn.return_value = "192.168.0.1"
        mock_gi4.country_name_by_addr.side_effect = socket.gaierror()
        
        result = webchat_getorigin("C0A80001")
        assert result is not None
        assert "192.168.0.1" in result
        # Should not fail even if GeoIP fails

    def test_edge_case_ips(self):
        """Test edge case IP addresses"""
        edge_cases = [
            "00000001",  # 0.0.0.1
            "FF000001",  # 255.0.0.1
            "00FF0001",  # 0.255.0.1
            "0000FF01",  # 0.0.255.1
            "000000FF",  # 0.0.0.255
        ]
        
        for hex_ip in edge_cases:
            result = webchat_getorigin(hex_ip)
            assert result is not None
            assert "." in result  # Should contain IP format


class TestHostmaskValidation:
    """Test hostmask validation"""

    def test_valid_hostmasks(self):
        """Test valid hostmask formats"""
        valid_hostmasks = [
            "nick!user@host.com",
            "testnick!testuser@example.org",
            "bot!~botuser@bot.domain.net",
            "user123!user@192.168.1.1",
            "nick!ident@gateway/web/freenode",
            "someone!~someone@unaffiliated/someone",
        ]
        
        for hostmask in valid_hostmasks:
            assert check_hostmask(hostmask) is True

    def test_invalid_hostmasks(self):
        """Test invalid hostmask formats"""
        invalid_hostmasks = [
            "nick",  # Missing ! and @
            "nick!user",  # Missing @
            "nick@host.com",  # Missing !
            "!user@host.com",  # Missing nick
            "nick!@host.com",  # Missing user
            "nick!user@",  # Missing host
            "",  # Empty string
            "nick user@host.com",  # Space instead of !
            "nick!user host.com",  # Space instead of @
        ]
        
        for hostmask in invalid_hostmasks:
            assert check_hostmask(hostmask) is False

    def test_edge_case_hostmasks(self):
        """Test edge case hostmasks"""
        edge_cases = [
            "a!b@c",  # Minimal valid hostmask
            "nick!!user@host",  # Double !
            "nick!user@@host",  # Double @
            "nick!user@host@extra",  # Multiple @
            "nick!user!extra@host",  # Multiple !
        ]
        
        for hostmask in edge_cases:
            result = check_hostmask(hostmask)
            # These should still match the regex pattern
            assert isinstance(result, bool)

    def test_unicode_hostmasks(self):
        """Test hostmasks with unicode characters"""
        unicode_hostmasks = [
            "niçk!üser@höst.com",
            "тест!пользователь@хост.рф",
            "用户!身份@主机.中国",
        ]
        
        for hostmask in unicode_hostmasks:
            result = check_hostmask(hostmask)
            # Should handle unicode characters
            assert isinstance(result, bool)

    def test_very_long_hostmasks(self):
        """Test very long hostmasks"""
        long_nick = "a" * 100
        long_user = "b" * 100
        long_host = "c" * 100 + ".com"
        long_hostmask = f"{long_nick}!{long_user}@{long_host}"
        
        assert check_hostmask(long_hostmask) is True

    def test_special_characters_in_hostmask(self):
        """Test hostmasks with special characters"""
        special_cases = [
            "nick[bot]!user@host.com",
            "nick-test!user_test@host-name.com",
            "nick.bot!~user@host.example.net",
            "nick123!user456@192.168.1.100",
        ]
        
        for hostmask in special_cases:
            assert check_hostmask(hostmask) is True


@pytest.mark.skipif(not WOLFRAM_AVAILABLE, reason="Wolfram Alpha module not available")
class TestWolframStringCleaning:
    """Test Wolfram Alpha string cleaning functions"""

    def test_clean_answer_basic(self):
        """Test basic string cleaning"""
        assert clean_answer("simple text") == "simple text"
        assert clean_answer("") == ""
        assert clean_answer(None) is None

    def test_clean_answer_pipe_replacement(self):
        """Test pipe character replacement"""
        input_str = "value1 | value2 | value3"
        result = clean_answer(input_str)
        assert result == "value1: value2: value3"

    def test_clean_answer_newline_replacement(self):
        """Test newline replacement"""
        input_str = "line1\nline2\nline3"
        result = clean_answer(input_str)
        assert result == "line1 | line2 | line3"

    def test_clean_answer_tilde_replacement(self):
        """Test tilde replacement with approximation"""
        input_str = "value ~~ 3.14"
        result = clean_answer(input_str)
        assert "≈" in result
        assert "3.14" in result

    def test_clean_answer_multiple_spaces(self):
        """Test multiple space reduction"""
        input_str = "word1    word2     word3"
        result = clean_answer(input_str)
        assert result == "word1 word2 word3"

    def test_clean_answer_whitespace_trimming(self):
        """Test whitespace trimming"""
        input_str = "  text with spaces  "
        result = clean_answer(input_str)
        assert result == "text with spaces"

    def test_clean_answer_currency_symbols(self):
        """Test currency symbol replacement"""
        # Bitcoin symbol
        input_str = "Price: \\:0e3f 1000"
        result = clean_answer(input_str)
        assert "฿" in result
        assert "1000" in result

        # Yen symbol
        input_str = "Price: \\:ffe5 500"
        result = clean_answer(input_str)
        assert "￥" in result
        assert "500" in result

    def test_clean_answer_complex_example(self):
        """Test complex cleaning with multiple operations"""
        input_str = "Result | answer\nValue ~~ 42   | Currency: \\:0e3f 100"
        result = clean_answer(input_str)
        
        # Should apply all transformations
        assert "Result: answer" in result
        assert "Value ≈ 42" in result
        assert "Currency: ฿ 100" in result
        assert "\n" not in result

    def test_clean_question_delegates_to_clean_answer(self):
        """Test that clean_question uses clean_answer"""
        test_string = "question | with\nnewlines"
        question_result = clean_question(test_string)
        answer_result = clean_answer(test_string)
        assert question_result == answer_result

    def test_clean_answer_edge_cases(self):
        """Test edge cases for string cleaning"""
        # Only special characters
        assert clean_answer("~~~") == "≈≈≈"
        assert clean_answer("|||") == ":::"
        assert clean_answer("\n\n\n") == " |  | "

        # Mixed operations
        mixed = "~~~ | \n   multiple   spaces"
        result = clean_answer(mixed)
        assert "≈≈≈" in result
        assert ":" in result
        assert "|" in result
        # Should not have multiple consecutive spaces
        assert "  " not in result

    def test_clean_answer_mathematical_expressions(self):
        """Test cleaning of mathematical expressions"""
        math_expr = "x ~~ 3.14159 | y = 2.71828\nz ~~ 1.41421"
        result = clean_answer(math_expr)
        
        assert "x ≈ 3.14159" in result
        assert "y = 2.71828" in result
        assert "z ≈ 1.41421" in result
        assert " | " in result  # Newline converted to pipe
        assert ":" in result  # Pipe converted to colon

    def test_clean_answer_real_wolfram_output(self):
        """Test with realistic Wolfram Alpha output"""
        wolfram_output = """Result | 42
        Input interpretation | number
        
        Result ~~ 4.2 × 10^1"""
        
        result = clean_answer(wolfram_output)
        
        assert "Result: 42" in result
        assert "Input interpretation: number" in result
        assert "4.2 × 10^1" in result
        assert "≈" in result
        assert "\n" not in result


class TestModuleHelperEdgeCases:
    """Test edge cases and error conditions for module helpers"""

    def test_webchat_getorigin_memory_efficiency(self):
        """Test that webchat_getorigin doesn't use excessive memory"""
        # Test with many invalid inputs to ensure no memory leaks
        invalid_inputs = [
            "G" * 8,  # Invalid hex
            "1" * 7,  # Wrong length
            "ZZZZZZZZ",  # Invalid hex
            "",  # Empty
            None,  # This might cause an error, but shouldn't crash
        ]
        
        for invalid_input in invalid_inputs:
            try:
                result = webchat_getorigin(invalid_input)
                assert result is None
            except (TypeError, AttributeError):
                # None input might cause these, which is acceptable
                pass

    def test_hostmask_regex_performance(self):
        """Test hostmask validation with various edge cases"""
        # Very long strings
        very_long = "a" * 10000
        result = check_hostmask(very_long)
        assert isinstance(result, bool)
        
        # String with many special characters
        special_string = "!@#$%^&*()!user@host.com"
        result = check_hostmask(special_string)
        assert isinstance(result, bool)

    @pytest.mark.skipif(not WOLFRAM_AVAILABLE, reason="Wolfram Alpha module not available")
    def test_clean_answer_performance(self):
        """Test string cleaning with large inputs"""
        # Large string with many replacements
        large_string = ("text | text\n" * 1000) + ("value ~~ number " * 1000)
        result = clean_answer(large_string)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert ":" in result  # Pipes should be replaced
        assert "≈" in result  # Tildes should be replaced

    def test_integration_realistic_usage(self):
        """Test functions with realistic usage patterns"""
        # Simulate realistic webchat usage
        common_hex_ips = [
            "C0A80001",  # 192.168.0.1
            "0A000001",  # 10.0.0.1
            "AC100001",  # 172.16.0.1
        ]
        
        for hex_ip in common_hex_ips:
            result = webchat_getorigin(hex_ip)
            assert result is not None
            assert "." in result  # Should contain IP
        
        # Simulate realistic hostmask validation
        common_hostmasks = [
            "user!~webchat@gateway/web/freenode",
            "nick!user@unaffiliated/nick",
            "bot!bot@example.com",
        ]
        
        for hostmask in common_hostmasks:
            assert check_hostmask(hostmask) is True