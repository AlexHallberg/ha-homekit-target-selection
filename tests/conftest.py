"""Fixtures for HomeKit Bridge custom component tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load the homekit integration from custom_components."""
    return
