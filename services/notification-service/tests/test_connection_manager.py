"""
Tests for ConnectionManager.
All WebSocket objects are mocked — no real connections needed.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.core.connection_manager import ConnectionManager


def _make_ws() -> MagicMock:
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_registers_connection(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        assert manager.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_connect_multiple_tabs_same_user(self):
        manager = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("user-1", ws1)
        await manager.connect("user-1", ws2)
        assert len(manager._active["user-1"]) == 2


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        manager.disconnect("user-1", ws)
        assert not manager.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_disconnect_unknown_user_does_not_raise(self):
        manager = ConnectionManager()
        ws = _make_ws()
        manager.disconnect("nonexistent", ws)  # should not raise

    @pytest.mark.asyncio
    async def test_disconnect_one_of_two_tabs(self):
        manager = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("user-1", ws1)
        await manager.connect("user-1", ws2)
        manager.disconnect("user-1", ws1)
        assert manager.is_connected("user-1")
        assert len(manager._active["user-1"]) == 1


class TestSendToUser:
    @pytest.mark.asyncio
    async def test_send_to_user_calls_send_json(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        await manager.send_to_user("user-1", {"type": "test"})
        ws.send_json.assert_called_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_send_to_offline_user_does_not_raise(self):
        manager = ConnectionManager()
        await manager.send_to_user("offline-user", {"type": "test"})

    @pytest.mark.asyncio
    async def test_broken_connection_is_removed(self):
        manager = ConnectionManager()
        ws = _make_ws()
        ws.send_json = AsyncMock(side_effect=Exception("Connection broken"))
        await manager.connect("user-1", ws)
        await manager.send_to_user("user-1", {"type": "test"})
        assert not manager.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_send_to_multiple_tabs(self):
        manager = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("user-1", ws1)
        await manager.connect("user-1", ws2)
        await manager.send_to_user("user-1", {"type": "test"})
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_users(self):
        manager = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect("user-1", ws1)
        await manager.connect("user-2", ws2)
        await manager.broadcast({"type": "incident_resolved", "incident_id": "inc-1"})
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections_does_not_raise(self):
        manager = ConnectionManager()
        await manager.broadcast({"type": "incident_resolved", "incident_id": "inc-1"})

    @pytest.mark.asyncio
    async def test_broadcast_correct_message(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        msg = {"type": "incident_resolved", "incident_id": "inc-999"}
        await manager.broadcast(msg)
        ws.send_json.assert_called_once_with(msg)


class TestIsConnected:
    @pytest.mark.asyncio
    async def test_returns_false_when_not_connected(self):
        manager = ConnectionManager()
        assert not manager.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_returns_true_when_connected(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        assert manager.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_returns_false_after_disconnect(self):
        manager = ConnectionManager()
        ws = _make_ws()
        await manager.connect("user-1", ws)
        manager.disconnect("user-1", ws)
        assert not manager.is_connected("user-1")