import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import ensure_directories
import backend.app.config as app_config
from backend.app.database import Base, get_db
import backend.app.services.pipeline_service as pipeline_service
from backend.app.main import app


@pytest.fixture(scope="function")
def test_env(tmp_path: Path):
    """Set up temporary database and storage paths for tests."""
    temp_storage = tmp_path / "test_storage"
    temp_uploads = temp_storage / "uploads"
    temp_outputs = temp_storage / "outputs"
    temp_uploads.mkdir(parents=True, exist_ok=True)
    temp_outputs.mkdir(parents=True, exist_ok=True)

    # Patch config storage paths
    orig_storage = app_config.STORAGE_DIR
    orig_upload = app_config.UPLOAD_DIR
    orig_output = app_config.OUTPUT_DIR

    app_config.STORAGE_DIR = temp_storage
    app_config.UPLOAD_DIR = temp_uploads
    app_config.OUTPUT_DIR = temp_outputs

    # Create test SQLite database
    db_file = temp_storage / "test_crowdahead.db"
    test_db_url = f"sqlite:///{db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch pipeline_service SessionLocal so background tasks use test DB
    orig_pipeline_session = pipeline_service.SessionLocal
    pipeline_service.SessionLocal = TestingSessionLocal

    # Create tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "engine": engine,
        "Session": TestingSessionLocal,
        "storage": temp_storage,
        "uploads": temp_uploads,
        "outputs": temp_outputs
    }

    # Teardown
    app.dependency_overrides.clear()
    pipeline_service.SessionLocal = orig_pipeline_session
    app_config.STORAGE_DIR = orig_storage
    app_config.UPLOAD_DIR = orig_upload
    app_config.OUTPUT_DIR = orig_output


@pytest.fixture(scope="function")
def client(test_env):
    """FastAPI TestClient configured with test database and isolated storage."""
    with TestClient(app) as test_client:
        yield test_client
