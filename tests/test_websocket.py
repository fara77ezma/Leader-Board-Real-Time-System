import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import WebSocketDisconnect

from controllers.websocket import connect_to_ws


class TestConnectToWs:
    @pytest.mark.asyncio
    async def test_successful_connection_and_initial_send(self, mocker):
        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(1000)

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mock_leaderboard_data = {
            "game_name": "space_race",
            "leaderboard": [
                {"rank": 1, "username": "alice", "score": 100},
                {"rank": 2, "username": "bob", "score": 90},
            ],
        }

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value=mock_leaderboard_data,
        )

        mock_db = Mock()

        await connect_to_ws(mock_websocket, "space_race", mock_db)

        mock_manager.connect.assert_called_once_with(
            websocket=mock_websocket, game_name="space_race"
        )
        mock_websocket.send_json.assert_called_once_with(mock_leaderboard_data)
        mock_manager.disconnect.assert_called_once_with(
            websocket=mock_websocket, game_name="space_race"
        )

    @pytest.mark.asyncio
    async def test_connection_with_empty_leaderboard(self, mocker):
        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(1000)

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mock_leaderboard_data = {"game_name": "new_game", "leaderboard": []}

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value=mock_leaderboard_data,
        )

        mock_db = Mock()

        await connect_to_ws(mock_websocket, "new_game", mock_db)

        mock_websocket.send_json.assert_called_once_with(mock_leaderboard_data)

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handled(self, mocker):
        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(1000)

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value={"game_name": "space_race", "leaderboard": []},
        )

        mock_db = Mock()

        await connect_to_ws(mock_websocket, "space_race", mock_db)

        # Should not raise exception
        mock_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_connect_called_with_correct_params(self, mocker):
        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = WebSocketDisconnect(1000)

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value={"game_name": "chess_master", "leaderboard": []},
        )

        mock_db = Mock()

        await connect_to_ws(mock_websocket, "chess_master", mock_db)

        # Verify manager.connect called with game_name
        call_args = mock_manager.connect.call_args
        assert call_args[1]["game_name"] == "chess_master"
        assert call_args[1]["websocket"] == mock_websocket

    @pytest.mark.asyncio
    async def test_db_query_failure_during_connection(self, mocker):
        mock_websocket = AsyncMock()
        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            side_effect=Exception("DB error"),
        )

        mock_db = Mock()

        with pytest.raises(Exception) as exc_info:
            await connect_to_ws(mock_websocket, "space_race", mock_db)

        assert "DB error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_send_json_failure(self, mocker):
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Send failed")

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value={"game_name": "space_race", "leaderboard": []},
        )

        mock_db = Mock()

        with pytest.raises(Exception) as exc_info:
            await connect_to_ws(mock_websocket, "space_race", mock_db)

        assert "Send failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_multiple_messages_received_before_disconnect(self, mocker):
        mock_websocket = AsyncMock()
        # Simulate receiving 3 messages, then disconnect
        mock_websocket.receive_text.side_effect = [
            "msg1",
            "msg2",
            "msg3",
            WebSocketDisconnect(1000),
        ]

        mock_manager = Mock()
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = Mock()

        mocker.patch("controllers.websocket.manager", mock_manager)
        mocker.patch(
            "controllers.websocket.leaderboard.fetch_leaderboard",
            return_value={"game_name": "space_race", "leaderboard": []},
        )

        mock_db = Mock()

        await connect_to_ws(mock_websocket, "space_race", mock_db)

        # Verify receive_text was called multiple times
        assert mock_websocket.receive_text.call_count >= 4
        mock_manager.disconnect.assert_called_once()
