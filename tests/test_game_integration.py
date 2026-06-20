class TestGameEndpointAuth:
    def test_non_admin_cannot_create_game(self, client, register_verified_user):
        """Test that non-admin user cannot create game"""
        user = register_verified_user(
            username="regularuser",
            email="regular@example.com",
            phone_number="01012345680",
        )

        response = client.post(
            "/game/",
            headers=user["headers"],
            json={"name": "test_game", "description": "Test game"},
        )

        assert response.status_code == 403

    def test_non_admin_cannot_get_all_games(self, client, register_verified_user):
        """Test that non-admin user cannot get all games"""
        user = register_verified_user(
            username="regularuser",
            email="regular@example.com",
            phone_number="01012345681",
        )

        response = client.get(
            "/game/",
            headers=user["headers"],
        )

        assert response.status_code == 403

    def test_non_admin_cannot_deactivate_game(
        self, client, register_verified_user, mock_existing_game
    ):
        """Test that non-admin user cannot deactivate game"""
        mock_existing_game(name="test_game")
        user = register_verified_user(
            username="regularuser",
            email="regular@example.com",
            phone_number="01012345682",
        )

        response = client.patch(
            "/game/deactivate/test_game",
            headers=user["headers"],
        )

        assert response.status_code == 403

    def test_non_admin_cannot_activate_game(
        self, client, register_verified_user, mock_existing_game
    ):
        """Test that non-admin user cannot activate game"""
        mock_existing_game(name="test_game", is_active=False)
        user = register_verified_user(
            username="regularuser",
            email="regular@example.com",
            phone_number="01012345683",
        )

        response = client.patch(
            "/game/activate/test_game",
            headers=user["headers"],
        )

        assert response.status_code == 403

    def test_non_admin_cannot_delete_game(
        self, client, register_verified_user, mock_existing_game
    ):
        """Test that non-admin user cannot delete game"""
        mock_existing_game(name="test_game")
        user = register_verified_user(
            username="regularuser",
            email="regular@example.com",
            phone_number="01012345684",
        )

        response = client.delete(
            "/game/test_game",
            headers=user["headers"],
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_create_game(self, client):
        """Test that unauthenticated user cannot create game"""
        response = client.post(
            "/game/",
            json={"name": "test_game", "description": "Test game"},
        )

        assert response.status_code == 401


class TestGameCRUDFlow:
    def test_create_game_success(self, client, register_admin_user):
        """Test successfully creating a game"""
        admin = register_admin_user(
            username="admin1",
            email="admin1@example.com",
            phone_number="01000000000",
        )

        response = client.post(
            "/game/",
            headers=admin["headers"],
            json={
                "name": "space_race",
                "description": "Race through space",
                "is_active": True,
            },
        )

        assert response.status_code == 200
        assert response.json()["message"] == "New game created successfully."

    def test_get_all_games_includes_created_game(self, client, register_admin_user):
        """Test that newly created game appears in get all games"""
        admin = register_admin_user(
            username="admin2",
            email="admin2@example.com",
            phone_number="01000000001",
        )

        client.post(
            "/game/",
            headers=admin["headers"],
            json={"name": "space_race", "description": "Race through space"},
        )

        response = client.get(
            "/game/",
            headers=admin["headers"],
        )

        assert response.status_code == 200
        games = response.json()
        game_names = [g["name"] for g in games]
        assert "space_race" in game_names

    def test_get_active_games_public_endpoint(self, client, mock_existing_game):

        mock_existing_game(name="chess_master", is_active=True)

        response = client.get("/game/list")

        assert response.status_code == 200
        games = response.json()
        game_names = [g["name"] for g in games]
        assert "chess_master" in game_names

    def test_deactivate_game_success(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test successfully deactivating a game"""
        admin = register_admin_user(
            username="admin4",
            email="admin4@example.com",
            phone_number="01000000003",
        )
        mock_existing_game(name="space_race", is_active=True)

        response = client.patch(
            "/game/deactivate/space_race",
            headers=admin["headers"],
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Game deactivated successfully."

    def test_get_active_games_excludes_deactivated(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test that deactivated game doesn't appear in active games"""
        admin = register_admin_user(
            username="admin5",
            email="admin5@example.com",
            phone_number="01000000004",
        )
        mock_existing_game(name="old_game", is_active=True)

        client.patch(
            "/game/deactivate/old_game",
            headers=admin["headers"],
        )

        response = client.get("/game/list")

        game_names = [g["name"] for g in response.json()]
        assert "old_game" not in game_names

    def test_activate_game_success(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test successfully activating a game"""
        admin = register_admin_user(
            username="admin6",
            email="admin6@example.com",
            phone_number="01000000005",
        )
        mock_existing_game(name="space_race", is_active=False)

        response = client.patch(
            "/game/activate/space_race",
            headers=admin["headers"],
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Game activated successfully."

    def test_delete_game_success(self, client, register_admin_user, mock_existing_game):
        """Test successfully deleting a game"""
        admin = register_admin_user(
            username="admin7",
            email="admin7@example.com",
            phone_number="01000000006",
        )
        mock_existing_game(name="space_race")

        response = client.delete(
            "/game/space_race",
            headers=admin["headers"],
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Game deleted successfully."

    def test_deleted_game_not_in_all_games(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test that deleted game doesn't appear in all games"""
        admin = register_admin_user(
            username="admin8",
            email="admin8@example.com",
            phone_number="01000000007",
        )
        mock_existing_game(name="space_race")

        client.delete(
            "/game/space_race",
            headers=admin["headers"],
        )

        response = client.get(
            "/game/",
            headers=admin["headers"],
        )

        game_names = [g["name"] for g in response.json()]
        assert "space_race" not in game_names


class TestGameEdgeCases:
    def test_create_duplicate_game_name_returns_400(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test that creating game with duplicate name returns 400"""
        admin = register_admin_user(
            username="admin9",
            email="admin9@example.com",
            phone_number="01000000008",
        )
        mock_existing_game(name="space_race", is_active=True)

        response = client.post(
            "/game/",
            headers=admin["headers"],
            json={"name": "space_race"},
        )

        assert response.status_code == 400
        assert "Game with this name already exists" in response.json()["detail"]

    def test_reactivate_inactive_game_with_same_name(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test reactivating inactive game"""
        admin = register_admin_user(
            username="admin10",
            email="admin10@example.com",
            phone_number="01000000009",
        )
        mock_existing_game(name="space_race", is_active=False)

        response = client.post(
            "/game/",
            headers=admin["headers"],
            json={"name": "space_race"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Game reactivated successfully."

    def test_deactivate_nonexistent_game_returns_404(self, client, register_admin_user):
        """Test that deactivating non-existent game returns 404"""
        admin = register_admin_user(
            username="admin11",
            email="admin11@example.com",
            phone_number="01000000010",
        )

        response = client.patch(
            "/game/deactivate/nonexistent",
            headers=admin["headers"],
        )

        assert response.status_code == 404
        assert "Game not found" in response.json()["detail"]

    def test_activate_nonexistent_game_returns_404(self, client, register_admin_user):
        """Test that activating non-existent game returns 404"""
        admin = register_admin_user(
            username="admin12",
            email="admin12@example.com",
            phone_number="01000000011",
        )

        response = client.patch(
            "/game/activate/nonexistent",
            headers=admin["headers"],
        )

        assert response.status_code == 404
        assert "Game not found" in response.json()["detail"]

    def test_delete_nonexistent_game_returns_404(self, client, register_admin_user):
        """Test that deleting non-existent game returns 404"""
        admin = register_admin_user(
            username="admin13",
            email="admin13@example.com",
            phone_number="01000000012",
        )

        response = client.delete(
            "/game/nonexistent",
            headers=admin["headers"],
        )

        assert response.status_code == 404
        assert "Game not found" in response.json()["detail"]

    def test_deactivate_already_deactivated_game_returns_400(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test that deactivating already deactivated game returns 400"""
        admin = register_admin_user(
            username="admin14",
            email="admin14@example.com",
            phone_number="01000000013",
        )
        mock_existing_game(name="old_game", is_active=False)

        response = client.patch(
            "/game/deactivate/old_game",
            headers=admin["headers"],
        )

        assert response.status_code == 400
        assert "Game is already deactivated" in response.json()["detail"]

    def test_activate_already_active_game_returns_400(
        self, client, register_admin_user, mock_existing_game
    ):
        """Test that activating already active game returns 400"""
        admin = register_admin_user(
            username="admin15",
            email="admin15@example.com",
            phone_number="01000000014",
        )
        mock_existing_game(name="space_race", is_active=True)

        response = client.patch(
            "/game/activate/space_race",
            headers=admin["headers"],
        )

        assert response.status_code == 400
        assert "Game is already active" in response.json()["detail"]
