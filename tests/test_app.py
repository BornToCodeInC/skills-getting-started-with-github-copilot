import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))

    yield

    # Cleanup
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


class TestRootEndpoint:
    def test_root_redirects_to_static_index(self):
        # Arrange
        path = "/"

        # Act
        response = client.get(path, follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    def test_get_activities_returns_all_activity_data(self):
        # Arrange
        expected_activity_names = {"Chess Club", "Programming Class", "Gym Class"}

        # Act
        response = client.get("/activities")
        payload = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(payload, dict)
        assert expected_activity_names.issubset(payload.keys())

    def test_get_activities_includes_required_fields(self):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")
        payload = response.json()
        activity = payload[activity_name]

        # Assert
        assert response.status_code == 200
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    def test_signup_adds_new_participant(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        original_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == original_count + 1

    def test_signup_returns_404_for_unknown_activity(self):
        # Arrange
        activity_name = "Does Not Exist"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_returns_400_for_duplicate_email(self):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestUnregisterParticipantEndpoint:
    def test_unregister_removes_participant_from_activity(self):
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_unregister_returns_404_for_unknown_activity(self):
        # Arrange
        activity_name = "Does Not Exist"
        email = "test@example.com"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_returns_404_for_missing_student(self):
        # Arrange
        activity_name = "Chess Club"
        email = "missing@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not found in this activity"
