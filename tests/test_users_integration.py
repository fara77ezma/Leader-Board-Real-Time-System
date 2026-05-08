from unittest.mock import AsyncMock


def test_user_profile_and_avatar_flow(
    client,
    register_verified_user,
    get_user,
    mocker,
):
    user = register_verified_user(
        username="avataruser",
        email="avataruser@example.com",
        phone_number="01012345679",
    )

    profile_response = client.get(
        "/users/api/profile",
        headers=user["headers"],
    )
    assert profile_response.status_code == 200
    profile_body = profile_response.json()
    assert profile_body["username"] == "avataruser"
    assert profile_body["is_verified"] is True
    assert profile_body["avatar_url"].startswith("https://ui-avatars.com/api/")
    assert profile_body["games"] == {}

    public_profile_response = client.get("/users/api/profile/avataruser")
    assert public_profile_response.status_code == 200
    assert public_profile_response.json()["username"] == "avataruser"

    upload_avatar = mocker.patch(
        "controllers.users.upload_avatar",
        new=AsyncMock(return_value="https://cdn.example.com/avataruser.png"),
    )

    update_response = client.put(
        "/users/api/profile",
        headers=user["headers"],
        files={"avatar_file": ("avatar.png", b"fake image bytes", "image/png")},
    )
    assert update_response.status_code == 200
    assert update_response.json() == {"message": "avatar updated successfully."}
    upload_avatar.assert_awaited_once()
    assert get_user("avataruser").avatar_url == "https://cdn.example.com/avataruser.png"

    updated_profile_response = client.get(
        "/users/api/profile",
        headers=user["headers"],
    )
    assert updated_profile_response.status_code == 200
    assert (
        updated_profile_response.json()["avatar_url"]
        == "https://cdn.example.com/avataruser.png"
    )

    delete_avatar = mocker.patch(
        "controllers.users.delete_avatar",
        new=AsyncMock(return_value=None),
    )

    delete_response = client.delete(
        "/users/api/profile/avatar",
        headers=user["headers"],
    )
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "avatar deleted successfully."}
    delete_avatar.assert_awaited_once_with("avataruser")
    assert get_user("avataruser").avatar_url.startswith("https://ui-avatars.com/api/")
