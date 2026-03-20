import socket
from unittest.mock import patch, MagicMock
import pytest
from meshcloud.networking import discovery

class TestPeerDiscovery:
    
    @patch("meshcloud.networking.discovery.add_peer")
    def test_seed_peers_from_config_success(self, mock_add_peer):
        """Test seeding peers from a valid config file."""
        # Prepare mock config data
        peers_data = {"peers": ["https://node1:8000", "https://node2:8000"]}
        
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            # Mock file context manager
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch("json.load", return_value=peers_data):
                discovery.seed_peers_from_config()
                
        # Verify add_peer was called for each peer
        assert mock_add_peer.call_count == 2
        mock_add_peer.assert_any_call("https://node1:8000")
        mock_add_peer.assert_any_call("https://node2:8000")

    @patch("meshcloud.networking.discovery.add_peer")
    def test_seed_peers_from_config_file_not_found(self, mock_add_peer):
        """Test graceful handling when config file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            discovery.seed_peers_from_config()
            
        mock_add_peer.assert_not_called()

    @patch("meshcloud.networking.discovery.add_peer")
    @patch("socket.getaddrinfo")
    @patch("time.sleep")
    def test_dns_discovery_worker(self, mock_sleep, mock_getaddrinfo, mock_add_peer):
        """Test DNS discovery worker functionality."""
        # Break the infinite loop
        mock_sleep.side_effect = InterruptedError("Stop loop") 
        
        # Mock DNS resolution
        # getaddrinfo returns list of (family, type, proto, canonname, sockaddr)
        # sockaddr is (address, port) for IPv4
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 8000)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.2', 8000))
        ]
        
        # Patch the configuration in app.main
        # We set THIS_NODE to match one of the IPs to ensure it filters itself out
        with patch("meshcloud.networking.discovery.DNS_DISCOVERY_SERVICE", "mesh-headless"), \
             patch("meshcloud.networking.discovery.THIS_NODE", "http://10.0.0.1:8000"): 
            
            try:
                discovery.dns_discovery_worker()
            except InterruptedError:
                pass
        
        # Verify interactions
        mock_getaddrinfo.assert_called_with("mesh-headless", 8000, proto=socket.IPPROTO_TCP)
        
        # Should call add_peer for 10.0.0.2 (10.0.0.1 matches THIS_NODE)
        mock_add_peer.assert_called_once_with("http://10.0.0.2:8000")

    @patch("meshcloud.networking.discovery.add_peer")
    @patch("time.sleep")
    def test_dns_discovery_disabled(self, mock_sleep, mock_add_peer):
        """Test that worker does nothing if DNS_DISCOVERY_SERVICE is not set."""
        with patch("meshcloud.networking.discovery.DNS_DISCOVERY_SERVICE", None):
            discovery.dns_discovery_worker()
            
        # Should exit immediately without sleeping or adding peers
        mock_add_peer.assert_not_called()