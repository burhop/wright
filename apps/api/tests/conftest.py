import os
import tempfile
import pytest

# Create a temporary SQLite database for the test session
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix="-test.db")
os.close(temp_db_fd)

# Set the environment variables before importing any application code
os.environ["DATABASE_PATH"] = temp_db_path

@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    monkeypatch.setenv("WRIGHT_TESTING", "1")

@pytest.fixture(scope="session", autouse=True)
def run_api_migrations():
    # Make sure we import run_migrations after setting DATABASE_PATH
    from api.database.migrate import run_migrations
    run_migrations()
    
    yield
    
    # Cleanup temp database
    if os.path.exists(temp_db_path):
        try:
            os.unlink(temp_db_path)
        except Exception:
            pass
