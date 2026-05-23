def test_leaderboard_submit_rank_and_profile_games_flow(
    client,
    register_verified_user,
):
    alice = register_verified_user(
        username="alice",
        email="alice@example.com",
        phone_number="01012345670",
    )
    bob = register_verified_user(
        username="bob",
        email="bob@example.com",
        phone_number="01012345671",
    )

    alice_first_score = client.post(
        "/leaderboard/api/submit-score",
        headers=alice["headers"],
        json={"game_name": "space_race", "score": 100},
    )
    assert alice_first_score.status_code == 200
    assert alice_first_score.json()["rank"] == 1

    bob_high_score = client.post(
        "/leaderboard/api/submit-score",
        headers=bob["headers"],
        json={"game_name": "space_race", "score": 250},
    )
    assert bob_high_score.status_code == 200
    assert bob_high_score.json()["rank"] == 1

    alice_new_best = client.post(
        "/leaderboard/api/submit-score",
        headers=alice["headers"],
        json={"game_name": "space_race", "score": 300},
    )
    assert alice_new_best.status_code == 200
    assert alice_new_best.json()["previous_best"] == 100.0
    assert alice_new_best.json()["rank"] == 1

    bob_lower_score = client.post(
        "/leaderboard/api/submit-score",
        headers=bob["headers"],
        json={"game_name": "space_race", "score": 200},
    )
    assert bob_lower_score.status_code == 200
    assert bob_lower_score.json()["best_score"] == 250.0
    assert bob_lower_score.json()["rank"] == 2

    leaderboard_response = client.get(
        "/leaderboard/api/get-leaderboard/space_race",
        params={"limit": 10},
    )
    assert leaderboard_response.status_code == 200
    assert leaderboard_response.json() == {
        "game_name": "space_race",
        "leaderboard": [
            {"rank": 1, "username": "alice", "score": 300.0},
            {"rank": 2, "username": "bob", "score": 250.0},
        ],
    }

    alice_rank_response = client.get(
        "/leaderboard/api/get-leaderboard/space_race/user-rank",
        headers=alice["headers"],
    )
    assert alice_rank_response.status_code == 200
    assert alice_rank_response.json()["rank"] == 1
    assert alice_rank_response.json()["score"] == 300.0

    bob_rank_response = client.get(
        "/leaderboard/api/get-leaderboard/space_race/user-rank",
        headers=bob["headers"],
    )
    assert bob_rank_response.status_code == 200
    assert bob_rank_response.json()["rank"] == 2
    assert bob_rank_response.json()["score"] == 250.0

    bob_profile_response = client.get(
        "/users/api/profile",
        headers=bob["headers"],
    )
    assert bob_profile_response.status_code == 200
    assert bob_profile_response.json()["games"] == {
        "space_race": {"score": 250.0, "rank": 2}
    }
