"""Pytest configuration for integration tests."""

import os

import pytest


@pytest.fixture
def postgres_connection_string():
    """Get PostgreSQL connection string for tests.

    Uses environment variable if set, otherwise uses docker-compose defaults.
    """
    return os.getenv(
        "TEST_POSTGRES_CONNECTION",
        "postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test",
    )


@pytest.fixture
def test_api_key():
    """Get test API key from environment.

    Raises:
        pytest.skip: If API key is not set
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set - skipping integration test")
    return api_key
