import pytest
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.models.profile import UserProfile, ProviderProfile
from app.crud.profile import ProfileCRUD
from app.schemas.profile import (
    UserProfileCreate,
    UserProfileUpdate,
    ProviderProfileCreate,
    ProviderProfileUpdate,
)

# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_create_user_profile(db_session):
    """Test creating a user profile"""
    user_id = uuid.uuid4()
    profile_data = UserProfileCreate(user_id=user_id)

    profile = ProfileCRUD.create_user_profile(db_session, profile_data)

    assert getattr(profile, "user_id") == user_id
    assert getattr(profile, "average_rating") == 0.00
    assert getattr(profile, "total_ratings") == 0
    assert getattr(profile, "default_mode") == "NIN"


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_get_user_profile(db_session):
    """Test getting a user profile"""
    user_id = uuid.uuid4()
    profile_data = UserProfileCreate(user_id=user_id)

    # Create profile
    created_profile = ProfileCRUD.create_user_profile(db_session, profile_data)

    # Get profile
    retrieved_profile = ProfileCRUD.get_user_profile(db_session, user_id)

    assert retrieved_profile is not None
    assert getattr(retrieved_profile, "user_id") == user_id
    assert getattr(retrieved_profile, "profile_id") == getattr(
        created_profile, "profile_id"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_update_user_profile(db_session):
    """Test updating a user profile"""
    user_id = uuid.uuid4()
    profile_data = UserProfileCreate(user_id=user_id)

    # Create profile
    ProfileCRUD.create_user_profile(db_session, profile_data)

    # Update profile
    update_data = UserProfileUpdate(bio="Updated bio", default_mode="LAH")
    updated_profile = ProfileCRUD.update_user_profile(db_session, user_id, update_data)

    assert updated_profile is not None
    assert getattr(updated_profile, "bio") == "Updated bio"
    assert getattr(updated_profile, "default_mode") == "LAH"


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_update_rating(db_session):
    """Test updating user rating"""
    user_id = uuid.uuid4()
    profile_data = UserProfileCreate(user_id=user_id)

    # Create profile
    ProfileCRUD.create_user_profile(db_session, profile_data)

    # Update rating
    updated_profile = ProfileCRUD.update_rating(db_session, user_id, 4.5)

    assert updated_profile is not None
    assert getattr(updated_profile, "average_rating") == 4.5
    assert getattr(updated_profile, "total_ratings") == 1

    # Add another rating
    updated_profile = ProfileCRUD.update_rating(db_session, user_id, 3.5)

    assert getattr(updated_profile, "average_rating") == 4.0  # (4.5 + 3.5) / 2
    assert getattr(updated_profile, "total_ratings") == 2


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_create_provider_profile(db_session):
    """Test creating a provider profile"""
    user_id = uuid.uuid4()
    from decimal import Decimal

    provider_data = ProviderProfileCreate(
        user_id=user_id,
        service_radius_miles=Decimal("5.0"),
        vehicle_description="Blue Honda Civic",
        hourly_rate=Decimal("25.00"),
    )

    provider_profile = ProfileCRUD.create_provider_profile(db_session, provider_data)

    assert getattr(provider_profile, "user_id") == user_id
    assert getattr(provider_profile, "service_radius_miles") == Decimal("5.0")
    assert getattr(provider_profile, "vehicle_description") == "Blue Honda Civic"
    assert getattr(provider_profile, "hourly_rate") == Decimal("25.00")


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_get_provider_profile(db_session):
    """Test getting a provider profile"""
    user_id = uuid.uuid4()
    provider_data = ProviderProfileCreate(user_id=user_id)

    # Create provider profile
    created_profile = ProfileCRUD.create_provider_profile(db_session, provider_data)

    # Get provider profile
    retrieved_profile = ProfileCRUD.get_provider_profile(db_session, user_id)

    assert retrieved_profile is not None
    assert getattr(retrieved_profile, "user_id") == user_id
    assert getattr(retrieved_profile, "id") == getattr(created_profile, "id")


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
def test_update_provider_profile(db_session):
    """Test updating a provider profile"""
    user_id = uuid.uuid4()
    provider_data = ProviderProfileCreate(user_id=user_id)

    # Create provider profile
    ProfileCRUD.create_provider_profile(db_session, provider_data)

    # Update provider profile
    from decimal import Decimal

    update_data = ProviderProfileUpdate(
        service_radius_miles=Decimal("10.0"),
        hourly_rate=Decimal("30.00"),
        is_available="false",
    )
    updated_profile = ProfileCRUD.update_provider_profile(
        db_session, user_id, update_data
    )

    assert updated_profile is not None
    assert getattr(updated_profile, "service_radius_miles") == Decimal("10.0")
    assert getattr(updated_profile, "hourly_rate") == Decimal("30.00")
    assert getattr(updated_profile, "is_available") == "false"
