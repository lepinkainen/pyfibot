# -*- coding: utf-8 -*-
"""
Integration tests for URL title functionality using a minimal approach.
Tests the end-to-end URL title extraction without complex bot setup.
"""
import pytest
from unittest.mock import Mock, patch
import requests
from vcr import VCR
import os

from pyfibot.modules import module_urltitle

# VCR setup
VCR_RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "once")
my_vcr = VCR(
    path_transformer=VCR.ensure_suffix(".yaml"),
    cassette_library_dir="tests/cassettes/",
    record_mode=VCR_RECORD_MODE,
)


def test_url_title_basic_mock():
    """Test URL title extraction with a simple mock"""
    # Create a minimal bot mock
    bot = Mock()
    bot.config = {"module_urltitle": {}}
    bot.say.return_value = ("#channel", "message")
    
    # Mock get_url to return a simple HTML response
    mock_response = Mock()
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.content = b"""
    <html>
    <head>
        <title>Test Product - Hamam Hand Towel Kitchen Towel Sweet Navy 50x90cm 100% Cotton</title>
        <meta property="og:title" content="Hamam Hand Towel - Navy Blue Cotton Towel">
    </head>
    <body>
        <h1>Product Page</h1>
    </body>
    </html>
    """
    
    bot.get_url.return_value = mock_response
    
    # Initialize the module
    module_urltitle.init(bot)
    
    # Test URL
    url = "https://shop.example.com/products/test-product"
    
    # Call handle_url
    result = module_urltitle.handle_url(bot, "testuser", "#testchannel", url, url)
    
    # Verify bot.say was called
    bot.say.assert_called()
    
    # Check the message
    call_args = bot.say.call_args[0]
    channel = call_args[0]
    message = call_args[1]
    
    assert channel == "#testchannel"
    assert message.startswith("Title:")
    # Should use OpenGraph title when available
    assert "Hamam Hand Towel - Navy Blue Cotton Towel" in message


def test_url_title_no_og_title():
    """Test URL title extraction when only regular title is available"""
    bot = Mock()
    bot.config = {"module_urltitle": {}}
    bot.say.return_value = ("#channel", "message")
    
    # Mock get_url to return HTML with only regular title
    mock_response = Mock()
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.content = b"""
    <html>
    <head>
        <title>Simple Page Title</title>
    </head>
    <body>
        <h1>Content</h1>
    </body>
    </html>
    """
    
    bot.get_url.return_value = mock_response
    module_urltitle.init(bot)
    
    url = "https://example.com/simple"
    result = module_urltitle.handle_url(bot, "testuser", "#testchannel", url, url)
    
    bot.say.assert_called()
    call_args = bot.say.call_args[0]
    message = call_args[1]
    
    assert "Title: Simple Page Title" == message


@my_vcr.use_cassette
def test_saaren_taika_url_real():
    """Test the actual Saaren Taika URL with VCR recording"""
    # Create a simple requests-based function to get the URL
    def simple_get_url(url, params=None, headers=None, cookies=None):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if headers:
            session.headers.update(headers)
        if cookies:
            session.cookies.update(cookies)
        
        try:
            response = session.get(url, params=params)
            return response
        except requests.RequestException:
            return None
    
    # Test the URL directly  
    url = "https://shop.saarentaika.com/collections/hamam-pyyhkeet/products/hamam-kasipyyhe-keittiopyyhe-suloinen-navy-koko-50x90cm-100-puuvillaa-paino-125g-saaren-taika"
    
    response = simple_get_url(url)
    
    # Basic checks
    assert response is not None
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')
    
    # Check that we got some content
    assert len(response.content) > 1000  # Should be a substantial page
    
    # Check for expected content in the HTML
    content_str = response.content.decode('utf-8', errors='ignore')
    
    # Should contain product-related terms
    content_lower = content_str.lower()
    product_terms = ['hamam', 'pyyhe', 'navy', 'puuvilla']
    found_terms = [term for term in product_terms if term in content_lower]
    
    print(f"Found product terms: {found_terms}")
    print(f"Response status: {response.status_code}")
    print(f"Content type: {response.headers.get('content-type')}")
    print(f"Content length: {len(response.content)}")
    
    # Should find at least some product terms
    assert len(found_terms) >= 1, f"Expected to find product terms in content"


def test_url_title_with_actual_extraction():
    """Test URL title extraction using the actual extraction logic"""
    # Use the __get_bs function to test title extraction
    bot = Mock()
    bot.config = {"module_urltitle": {}}
    
    # Mock response with realistic Shopify content
    mock_response = Mock()
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.content = b"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hamam kasipyyhe / keittiopyyhe Suloinen Navy koko 50x90cm 100% puuvillaa paino 125g - Saaren Taika</title>
        <meta property="og:title" content="Hamam kasipyyhe / keittiopyyhe Suloinen Navy">
        <meta property="og:description" content="Kaunis hamam pyyhe 100% puuvillaa">
    </head>
    <body>
        <h1>Product Title</h1>
    </body>
    </html>
    """
    
    bot.get_url.return_value = mock_response
    
    # Test the internal __get_bs function
    module_urltitle.bot = bot
    bs = module_urltitle.__get_bs(bot, "https://example.com")
    
    assert bs is not None
    
    # Test title extraction
    og_title = bs.find("meta", {"property": "og:title"})
    regular_title = bs.find("title")
    
    assert og_title is not None
    assert regular_title is not None
    assert og_title["content"] == "Hamam kasipyyhe / keittiopyyhe Suloinen Navy"
    assert "Hamam kasipyyhe" in regular_title.text


def test_url_validation_edge_cases():
    """Test URL validation and edge cases"""
    bot = Mock()
    bot.config = {"module_urltitle": {}}
    module_urltitle.init(bot)
    
    # Test None URL
    result = module_urltitle.handle_url(bot, "user", "#channel", None, "message")
    assert result is None
    
    # Test non-string URL  
    result = module_urltitle.handle_url(bot, "user", "#channel", 123, "message")
    assert result is None
    
    # Test empty URL
    result = module_urltitle.handle_url(bot, "user", "#channel", "", "message")
    assert result is None
    
    # Test manual ignore
    result = module_urltitle.handle_url(bot, "user", "#channel", "http://example.com", "- http://example.com")
    assert result is None
    
    # Test Spotify ignore
    result = module_urltitle.handle_url(bot, "user", "#channel", "https://open.spotify.com/track/123", "https://open.spotify.com/track/123")
    assert result is None


if __name__ == "__main__":
    # Run a quick test
    test_url_title_basic_mock()
    print("Basic mock test passed!")