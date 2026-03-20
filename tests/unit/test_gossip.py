import pytest
from unittest.mock import patch, MagicMock
from meshcloud.networking.gossip import GossipProtocol

class TestGossipProtocol:
    @patch("meshcloud.networking.gossip.get_all_peers")
    @patch("meshcloud.networking.gossip.get_all_files")
    @patch("requests.post")
    @patch("meshcloud.networking.gossip.update_peer_status")
    def test_gossip_pulse_success(self, mock_update_status, mock_post, mock_get_all_files, mock_get_all_peers):
        # Setup mock data
        mock_get_all_peers.return_value = ["http://node1:8000", "http://node2:8000"]
        mock_file = MagicMock()
        mock_file.hash = "mockhash123"
        mock_get_all_files.return_value = [mock_file]
        
        # Mock successful post response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ack", "known_peers": ["http://node3:8000"]}
        mock_post.return_value = mock_response
        
        gossip = GossipProtocol("http://mynode:8000", "my_node_id")
        
        # Trigger a single pulse manually
        gossip.pulse()
        
        # Should have added node1 and node2 to known peers
        assert "http://node1:8000" in gossip.peers
        assert "http://node2:8000" in gossip.peers
        
        # Since node1 and node2 are in peers, it should have picked one to gossip with
        assert mock_post.called
        
        # Check payload
        call_args = mock_post.call_args
        url = call_args[0][0]
        json_payload = call_args[1]["json"]
        
        assert url in ["http://node1:8000/gossip", "http://node2:8000/gossip"]
        assert json_payload["sender"] == "http://mynode:8000"
        assert json_payload["node_id"] == "my_node_id"
        assert "mockhash123" in json_payload["files"]

    @patch("meshcloud.networking.gossip.update_peer_status")
    @patch("meshcloud.networking.gossip.register_file_location")
    def test_process_incoming_gossip(self, mock_register, mock_update_status):
        gossip = GossipProtocol("http://mynode:8000", "my_node_id")
        gossip.peers = {"http://nodeX:8000": {"score": 100, "status": "alive"}}
        
        payload = {
            "sender": "http://sender:8000",
            "files": ["hash1", "hash2"]
        }
        
        response = gossip.process_incoming_gossip(payload)
        
        assert response["status"] == "ack"
        assert "http://nodeX:8000" in response["known_peers"]
        
        assert mock_register.call_count == 2
        mock_register.assert_any_call("hash1", "http://sender:8000")
        mock_register.assert_any_call("hash2", "http://sender:8000")