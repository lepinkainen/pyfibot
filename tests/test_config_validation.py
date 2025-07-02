# -*- coding: utf-8 -*-
import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch, mock_open

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyfibot.pyfibot import validate_config, read_config


class TestConfigValidation:
    """Test configuration validation functionality"""

    def test_minimal_valid_config(self):
        """Test validation with minimal valid configuration"""
        config = {
            "networks": [
                {
                    "alias": "testnet",
                    "address": ["irc.example.com", 6667],
                    "nick": "testbot"
                }
            ]
        }
        
        # Mock the schema file reading
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["alias", "address", "nick"],
                        "properties": {
                            "alias": {"type": "string"},
                            "address": {"type": "array"},
                            "nick": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is True

    def test_missing_required_field(self):
        """Test validation with missing required field"""
        config = {
            # Missing required "networks" field
            "nick": "testbot"
        }
        
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {"type": "array"}
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is False

    def test_invalid_type(self):
        """Test validation with invalid field type"""
        config = {
            "networks": "not_an_array"  # Should be array
        }
        
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {"type": "array"}
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is False

    def test_valid_config_with_optional_fields(self):
        """Test validation with valid config including optional fields"""
        config = {
            "networks": [
                {
                    "alias": "testnet",
                    "address": ["irc.example.com", 6667],
                    "nick": "testbot"
                }
            ],
            "admins": ["admin!user@host.com"],
            "nick": "globalbot",
            "logging": {
                "debug": True
            }
        }
        
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["alias", "address", "nick"],
                        "properties": {
                            "alias": {"type": "string"},
                            "address": {"type": "array"},
                            "nick": {"type": "string"}
                        }
                    }
                },
                "admins": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "nick": {"type": "string"},
                "logging": {
                    "type": "object",
                    "properties": {
                        "debug": {"type": "boolean"}
                    }
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is True

    def test_admin_pattern_validation(self):
        """Test admin pattern validation from real schema"""
        config = {
            "networks": [{"alias": "test", "address": ["test.com", 6667], "nick": "bot"}],
            "admins": ["validuser!validident@validhost.com"]
        }
        
        # Use actual pattern from schema
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {"type": "array"},
                "admins": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^.+!.+@.+$"
                    }
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is True

    def test_invalid_admin_pattern(self):
        """Test invalid admin pattern"""
        config = {
            "networks": [{"alias": "test", "address": ["test.com", 6667], "nick": "bot"}],
            "admins": ["invalid_format"]  # Missing ! and @ separators
        }
        
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {"type": "array"},
                "admins": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^.+!.+@.+$"
                    }
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is False

    def test_schema_file_not_found(self):
        """Test behavior when schema file is not found"""
        config = {"networks": []}
        
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                validate_config(config)

    def test_invalid_json_schema(self):
        """Test behavior with invalid JSON schema file"""
        config = {"networks": []}
        
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("sys.path", ["/fake/path"]):
                with pytest.raises(json.JSONDecodeError):
                    validate_config(config)

    def test_complex_network_config(self):
        """Test validation of complex network configuration"""
        config = {
            "networks": [
                {
                    "alias": "freenode",
                    "address": ["irc.libera.chat", 6697],
                    "nick": "pyfibot",
                    "channels": ["#test", "#dev"],
                    "ssl": True,
                    "password": "secret"
                },
                {
                    "alias": "local",
                    "address": ["localhost", 6667],
                    "nick": "localbot",
                    "channels": ["#general"]
                }
            ]
        }
        
        mock_schema = {
            "type": "object",
            "required": ["networks"],
            "properties": {
                "networks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["alias", "address", "nick"],
                        "properties": {
                            "alias": {"type": "string"},
                            "address": {"type": "array"},
                            "nick": {"type": "string"},
                            "channels": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "ssl": {"type": "boolean"},
                            "password": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_schema))):
            with patch("sys.path", ["/fake/path"]):
                assert validate_config(config) is True


class TestConfigReading:
    """Test configuration file reading functionality"""

    def test_read_config_yaml_file(self):
        """Test reading a YAML configuration file"""
        yaml_content = """
networks:
  - alias: testnet
    address: [irc.example.com, 6667]
    nick: testbot
    channels:
      - "#test"
admins:
  - "admin!user@host.com"
nick: globalbot
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    config = read_config()
                    
                    assert "networks" in config
                    assert len(config["networks"]) == 1
                    assert config["networks"][0]["alias"] == "testnet"
                    assert config["admins"] == ["admin!user@host.com"]
                    assert config["nick"] == "globalbot"
            finally:
                os.unlink(f.name)

    def test_read_config_missing_file(self):
        """Test reading non-existent configuration file"""
        with patch("sys.argv", ["pyfibot.py", "nonexistent.yml"]):
            with pytest.raises(SystemExit):
                read_config()

    def test_read_config_invalid_yaml(self):
        """Test reading invalid YAML file"""
        invalid_yaml = """
networks:
  - alias: testnet
    address: [irc.example.com, 6667
    # Missing closing bracket - invalid YAML
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    with pytest.raises(SystemExit):
                        read_config()
            finally:
                os.unlink(f.name)

    def test_read_config_no_args(self):
        """Test reading config when no config file is specified"""
        with patch("sys.argv", ["pyfibot.py"]):
            with pytest.raises(SystemExit):
                read_config()

    def test_read_config_empty_file(self):
        """Test reading empty configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    config = read_config()
                    # Empty YAML file should return None, which becomes empty dict
                    assert config is None or config == {}
            finally:
                os.unlink(f.name)

    def test_read_config_yaml_with_comments(self):
        """Test reading YAML file with comments"""
        yaml_content = """
# PyFiBot configuration file
networks:
  # Main network
  - alias: testnet
    address: [irc.example.com, 6667]  # Standard IRC port
    nick: testbot
    channels:
      - "#test"  # Test channel

# Admin users (nick!user@host format)
admins:
  - "admin!user@host.com"

# Global bot nickname
nick: globalbot
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    config = read_config()
                    
                    assert "networks" in config
                    assert config["networks"][0]["alias"] == "testnet"
                    assert config["admins"] == ["admin!user@host.com"]
            finally:
                os.unlink(f.name)


class TestConfigEdgeCases:
    """Test edge cases in configuration handling"""

    def test_unicode_in_config(self):
        """Test configuration with unicode characters"""
        yaml_content = """
networks:
  - alias: tëstnet
    address: [irc.exämple.com, 6667]
    nick: tëstbot
    channels:
      - "#tëst"
admins:
  - "ädmin!üser@höst.com"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    config = read_config()
                    
                    assert config["networks"][0]["alias"] == "tëstnet"
                    assert config["networks"][0]["nick"] == "tëstbot"
                    assert config["admins"][0] == "ädmin!üser@höst.com"
            finally:
                os.unlink(f.name)

    def test_large_config_file(self):
        """Test with a large configuration file"""
        # Create config with many networks
        networks = []
        for i in range(50):
            networks.append({
                "alias": f"network_{i}",
                "address": [f"irc{i}.example.com", 6667],
                "nick": f"bot_{i}",
                "channels": [f"#channel_{j}" for j in range(10)]
            })
        
        config_dict = {
            "networks": networks,
            "admins": [f"admin{i}!user{i}@host{i}.com" for i in range(20)]
        }
        
        yaml_content = f"networks:\n"
        for net in networks:
            yaml_content += f"  - alias: {net['alias']}\n"
            yaml_content += f"    address: [{net['address'][0]}, {net['address'][1]}]\n"
            yaml_content += f"    nick: {net['nick']}\n"
            yaml_content += "    channels:\n"
            for chan in net['channels']:
                yaml_content += f"      - \"{chan}\"\n"
        
        yaml_content += "admins:\n"
        for admin in config_dict['admins']:
            yaml_content += f"  - \"{admin}\"\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with patch("sys.argv", ["pyfibot.py", f.name]):
                    config = read_config()
                    
                    assert len(config["networks"]) == 50
                    assert len(config["admins"]) == 20
                    assert config["networks"][0]["alias"] == "network_0"
                    assert config["networks"][49]["alias"] == "network_49"
            finally:
                os.unlink(f.name)