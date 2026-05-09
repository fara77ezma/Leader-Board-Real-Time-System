def test_full_auth_flow(client, get_user):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "flowuser",
            "email": "FlowUser@example.com",
            "password": "Secure@Pass123",
            "phone_number": "01012345678",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json() == {
        "message": "Registration successful. Please check your email to verify your account.",
        "requires_verification": True,
        "username": "flowuser",
    }

    user = get_user("flowuser")
    assert user is not None
    assert user.email == "flowuser@example.com"
    assert user.is_verified is False
    assert user.email_verification_code is not None

    login_before_verification = client.post(
        "/auth/login",
        json={"username": "flowuser", "password": "Secure@Pass123"},
    )
    assert login_before_verification.status_code == 403
    assert login_before_verification.json() == {
        "detail": "Email not verified. Please verify your email before logging in."
    }

    verify_response = client.get(
        "/auth/verify-email",
        params={"code": user.email_verification_code},
    )
    assert verify_response.status_code == 200
    assert verify_response.json() == {"message": "Email verified successfully."}

    login_response = client.post(
        "/auth/login",
        json={"username": "flowuser", "password": "Secure@Pass123"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["message"] == "Login successful."
    assert login_body["token"]

    profile_response = client.get(
        "/users/api/profile",
        headers={"Authorization": f"Bearer {login_body['token']}"},
    )
    assert profile_response.status_code == 200
    profile_body = profile_response.json()
    assert profile_body["username"] == "flowuser"
    assert profile_body["is_verified"] is True
    assert profile_body["games"] == {}

    forgot_password_response = client.post(
        "/auth/forgot-password",
        params={"email": "flowuser@example.com"},
    )
    assert forgot_password_response.status_code == 200
    assert forgot_password_response.json() == {
        "message": "Password reset email sent successfully."
    }

    user = get_user("flowuser")
    assert user.password_reset_code is not None

    reset_password_response = client.post(
        "/auth/reset-password",
        params={
            "code": user.password_reset_code,
            "new_password": "NewSecure@Pass456",
        },
    )
    assert reset_password_response.status_code == 200
    assert reset_password_response.json() == {"message": "Password reset successfully."}

    old_password_response = client.post(
        "/auth/login",
        json={"username": "flowuser", "password": "Secure@Pass123"},
    )
    assert old_password_response.status_code == 404
    assert old_password_response.json() == {"detail": "Invalid username or password."}

    new_password_response = client.post(
        "/auth/login",
        json={"username": "flowuser", "password": "NewSecure@Pass456"},
    )
    assert new_password_response.status_code == 200
    assert new_password_response.json()["message"] == "Login successful."
    assert new_password_response.json()["token"]
