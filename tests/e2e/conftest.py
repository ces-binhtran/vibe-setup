"""Pytest configuration for end-to-end tests."""

import os

import pytest


@pytest.fixture(scope="session")
def postgres_connection_string():
    """Get PostgreSQL connection string for E2E tests.

    Uses environment variable if set, otherwise uses docker-compose defaults.
    """
    return os.getenv(
        "TEST_POSTGRES_CONNECTION",
        "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
    )


@pytest.fixture(scope="session")
def gemini_api_key():
    """Get Gemini API key from environment.

    Raises:
        pytest.skip: If API key is not set
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set - skipping E2E test")
    return api_key
