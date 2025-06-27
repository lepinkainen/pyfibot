# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to Python path to ensure imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test the core command logic directly without complex imports
# We'll mock the botcore module to test its functionality


class MockBot:
    """Simple mock bot for testing core commands"""
    
    def __init__(self):
        self.factory = Mock()
        self.factory.isAdmin = Mock(return_value=True)
        self.factory.allBots = {}
        self.factory.ns = {}
        self.factory.reload_config = Mock()
        self.factory._unload_removed_modules = Mock()
        self.factory._loadmodules = Mock()
        
        self.network = Mock()
        self.network.alias = "testnet"
        self.network.channels = []
        self.pingAve = 0.5
        self.hasQuit = False
        
    def say(self, channel, message, length=None):
        """Mock say method"""
        return (channel, message)
    
    def quit(self, message):
        """Mock quit method"""
        pass


class TestCoreCommandsLogic:
    """Test the core command logic independently"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.bot = MockBot()
        
    def test_say_returns_tuple(self):
        """Test that say method returns expected tuple"""
        result = self.bot.say("#test", "hello")
        assert result == ("#test", "hello")
    
    def test_command_echo(self):
        """Test the echo command"""
        result = self.bot.command_echo("testuser", "#testchan", "hello world")
        # The say method in BotMock returns a tuple
        assert result == ("#testchan", "testuser: hello world")
    
    def test_command_ping(self):
        """Test the ping command"""
        self.bot.get_nick = Mock(return_value="testuser")
        result = self.bot.command_ping("testuser!test@example.com", "#testchan", "")
        expected_ping = int(self.bot.pingAve * 100.0)
        assert result == ("#testchan", f"testuser: My current ping is {expected_ping}ms")
    
    def test_command_rehash_admin_success(self):
        """Test rehash command with admin privileges - success case"""
        with patch('pyfibot.botcore.rebuild.updateInstance') as mock_update:
            with patch('pyfibot.botcore.log') as mock_log:
                result = self.bot.command_rehash("admin!test@example.com", "#testchan", "")
                
                # Verify the rebuild was called
                mock_update.assert_called_once_with(self.bot)
                # Verify modules were reloaded
                self.bot.factory._unload_removed_modules.assert_called_once()
                self.bot.factory._loadmodules.assert_called_once()
                # Verify success message
                assert result == ("#testchan", "Rehash OK")
    
    def test_command_rehash_with_conf(self):
        """Test rehash command with conf argument"""
        with patch('pyfibot.botcore.rebuild.updateInstance'):
            result = self.bot.command_rehash("admin!test@example.com", "#testchan", "conf")
            # Config reload should be called
            self.bot.factory.reload_config.assert_called_once()
            assert result == ("#testchan", "Configuration reloaded.")
    
    def test_command_rehash_non_admin(self):
        """Test rehash command without admin privileges"""
        self.bot.factory.isAdmin.return_value = False
        result = self.bot.command_rehash("user!test@example.com", "#testchan", "")
        # Should return None (no action taken)
        assert result is None
    
    def test_command_rehash_exception(self):
        """Test rehash command when an exception occurs"""
        with patch('pyfibot.botcore.rebuild.updateInstance', side_effect=Exception("Test error")):
            with patch('pyfibot.botcore.log') as mock_log:
                result = self.bot.command_rehash("admin!test@example.com", "#testchan", "")
                assert result == ("#testchan", "Rehash error: Test error")
                mock_log.error.assert_called_once()
    
    def test_say_not_implemented(self):
        """Test that the base say method raises NotImplementedError"""
        from pyfibot.botcore import CoreCommands
        core = CoreCommands()
        with pytest.raises(NotImplementedError):
            core.say("#test", "message")
    
    def test_command_join_admin_new_channel(self):
        """Test join command for a new channel"""
        # Setup mock bot for the network
        mock_bot = Mock()
        mock_bot.network = self.network
        mock_bot.network.channels = ["#existing"]
        mock_bot.join = Mock()
        self.bot.factory.allBots = {"testnet": mock_bot}
        
        result = self.bot.command_join("admin!test@example.com", "#testchan", "#newchan")
        mock_bot.join.assert_called_once_with("#newchan")
    
    def test_command_join_with_password(self):
        """Test join command with password"""
        mock_bot = Mock()
        mock_bot.network = self.network
        mock_bot.network.channels = []
        mock_bot.join = Mock()
        self.bot.factory.allBots = {"testnet": mock_bot}
        
        result = self.bot.command_join("admin!test@example.com", "#testchan", "#newchan secret")
        mock_bot.join.assert_called_once_with("#newchan", key="secret")
    
    def test_command_join_already_in_channel(self):
        """Test join command when already in channel"""
        mock_bot = Mock()
        mock_bot.network = self.network
        mock_bot.network.channels = ["#newchan"]
        self.bot.factory.allBots = {"testnet": mock_bot}
        
        result = self.bot.command_join("admin!test@example.com", "#testchan", "#newchan")
        assert result == ("#testchan", "I am already in #newchan on testnet.")
    
    def test_command_join_network_not_found(self):
        """Test join command with non-existent network"""
        self.bot.factory.allBots = {}
        result = self.bot.command_join("admin!test@example.com", "#testchan", "#newchan@badnet")
        assert result == ("#testchan", "I am not on that network.")
    
    def test_command_join_non_admin(self):
        """Test join command without admin privileges"""
        self.bot.factory.isAdmin.return_value = False
        result = self.bot.command_join("user!test@example.com", "#testchan", "#newchan")
        assert result is None
    
    def test_command_part_success(self):
        """Test part command success"""
        mock_bot = Mock()
        mock_bot.network = self.network
        mock_bot.network.channels = ["#testchan"]
        mock_bot.part = Mock()
        self.bot.factory.allBots = {"testnet": mock_bot}
        
        self.bot.command_part("admin!test@example.com", "#testchan", "#testchan")
        mock_bot.part.assert_called_once_with("#testchan")
        assert "#testchan" not in mock_bot.network.channels
    
    def test_command_part_not_in_channel(self):
        """Test part command when not in channel"""
        mock_bot = Mock()
        mock_bot.network = self.network
        mock_bot.network.channels = ["#other"]
        self.bot.factory.allBots = {"testnet": mock_bot}
        
        with patch('pyfibot.botcore.log') as mock_log:
            self.bot.command_part("admin!test@example.com", "#testchan", "#nothere")
            mock_log.debug.assert_called()
    
    def test_command_leave_alias(self):
        """Test that leave is an alias for part"""
        with patch.object(self.bot, 'command_part') as mock_part:
            self.bot.command_leave("user", "#chan", "args")
            mock_part.assert_called_once_with("user", "#chan", "args")
    
    def test_command_quit_admin(self):
        """Test quit command with admin privileges"""
        self.bot.quit = Mock()
        self.bot.command_quit("admin!test@example.com", "#testchan", "")
        self.bot.quit.assert_called_once_with("Working as programmed")
        assert self.bot.hasQuit == 1
    
    def test_command_quit_non_admin(self):
        """Test quit command without admin privileges"""
        self.bot.factory.isAdmin.return_value = False
        self.bot.quit = Mock()
        result = self.bot.command_quit("user!test@example.com", "#testchan", "")
        self.bot.quit.assert_not_called()
        assert result is None
    
    def test_command_channels_no_args(self):
        """Test channels command without arguments"""
        self.bot.factory.allBots = {"net1": Mock(), "net2": Mock()}
        result = self.bot.command_channels("user", "#testchan", "")
        assert result == ("#testchan", "Please specify a network: net1, net2")
    
    def test_command_channels_with_args(self):
        """Test channels command with network argument"""
        self.bot.network.channels = ["#chan1", "#chan2"]
        result = self.bot.command_channels("user", "#testchan", "testnet")
        assert result == ("#testchan", "I am on ['#chan1', '#chan2']")
    
    def test_command_help_no_args(self):
        """Test help command without arguments"""
        # Mock namespace with some commands
        self.bot.factory.ns = {
            "module1": ({}, {
                "command_test": Mock(__doc__="Test command"),
                "admin_admin": Mock(__doc__="Admin command")
            })
        }
        self.bot.factory.isAdmin.return_value = True
        
        result = self.bot.command_help("admin!test@example.com", "#testchan", "")
        assert result == ("#testchan", "Available commands: test")
    
    def test_command_help_specific_command(self):
        """Test help command for specific command"""
        mock_cmd = Mock()
        mock_cmd.__doc__ = "Test command does something\nMore details here"
        
        self.bot.factory.ns = {
            "module1": ({}, {"command_test": mock_cmd})
        }
        
        result = self.bot.command_help("user", "#testchan", "test")
        assert result == ("#testchan", "Help for test: Test command does something")


class TestBotMock:
    """Test the BotMock class functionality"""
    
    def test_bot_mock_initialization(self):
        """Test BotMock initialization"""
        config = {"cmdchar": "!"}
        
        # Test basic initialization
        bot = bot_mock.BotMock(config)
        assert bot.config == config
        
    def test_bot_mock_say(self):
        """Test BotMock say method"""
        bot = bot_mock.BotMock()
        result = bot.say("#channel", "test message")
        assert result == ("#channel", "test message")