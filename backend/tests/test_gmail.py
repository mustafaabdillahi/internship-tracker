from app.config import Settings
from app.main import settings
from fastapi.testclient import TestClient
from jose import jwt
from unittest.mock import MagicMock, patch

def create_session_token(user_id: str, settings: Settings) -> str:
    """Returns a session JWT created the same away as the application."""
    payload = {"sub": user_id}
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256"
    )


def test_gmail_sync_without_session(client: TestClient):
    """Tests whether POST /gmail/sync returns status code 400 when there is no session."""
    response = client.post("/gmail/sync")
    assert response.status_code == 401


def test_gmail_sync_user_not_found(client: TestClient):
    """Tests whether POST /gmail/sync returns status code 404 when the user is non-existent."""
    session_token = create_session_token("TESTTEST", settings)

    # Simulates using mock:
    # db.query(User).filter(...).first()
    # returning None.
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Simulates "with SessionLocal() as db:" session
    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_db
    mock_session.__exit__.return_value = None

    with patch("app.main.SessionLocal", return_value=mock_session):
        response = client.post(
            "/gmail/sync",
            cookies={"session": session_token}
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_gmail_sync_google_account_not_connected(client: TestClient):
    """Tests whether POST /gmail/sync returns status code 400 when the user does not have
    a Google account connected."""
    user = MagicMock()
    user.id = "TESTTEST"
    user.email = "test@example.com"
    user.google_refresh_token = None

    session_token = create_session_token(user.id, settings)
    mock_db = MagicMock()

    # Simulates finding the user.
    mock_db.query.return_value.filter.return_value.first.return_value = user

    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_db
    mock_session.__exit__.return_value = None

    with patch("app.main.SessionLocal", return_value=mock_session):
        response = client.post(
            "/gmail/sync",
            cookies={"session": session_token},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Google account is not connected."


def test_gmail_sync_success(client: TestClient):
    """Tests whether POST /gmail/sync runs successfully and returns status code 200 when
    inputs are valid."""
    user = MagicMock()
    user.id = "TESTTEST"
    user.email = "test@example.com"
    user.google_refresh_token = "fake-refresh-token"

    session_token = create_session_token(user.id, settings)
    mock_db = MagicMock()

    fake_emails = [
        {
            "id": "email-1",
            "subject": "Hello",
            "sender": "sender@fake.com",
            "recipient": "recipient@fake.com"
        },
        {
            "id": "email-2",
            "subject": "Meeting",
            "sender": "sender@fake.com",
            "recipient": "recipient@fake.com"
        },
    ]

    # Simulate finding the fake user:
    # db.query(User)
    #   .filter(...)
    #   .first()
    # -> user
    mock_db.query.return_value.filter.return_value.first.return_value = user

    mock_session = MagicMock()
    mock_session.__enter__.return_value = mock_db
    mock_session.__exit__.return_value = None

    with patch(
        "app.main.SessionLocal", return_value=mock_session
    ), patch(
        "app.main.utils.get_emails", return_value=fake_emails
    ) as mock_get_emails, patch(
        "app.main.utils.write_email_records", return_value=2
    ) as mock_write_email_records:
        response = client.post(
            "/gmail/sync",
            cookies={"session": session_token},
        )

    # Test HTTP response
    assert response.status_code == 200
    assert response.json() == {
        "DEBUG": "Success. 2 emails recorded."
    }

    # Test Gmail function was called
    mock_get_emails.assert_called_once()

    # Test database writing function was called
    mock_write_email_records.assert_called_once()

    # Test arguments passed to write_email_records()
    args = mock_write_email_records.call_args.args
    assert args[0] == fake_emails
    assert args[1] == user
    assert args[2] == mock_db

    # Test database was committed
    mock_db.commit.assert_called_once()

    # Test user was refreshed
    mock_db.refresh.assert_called_once_with(user)