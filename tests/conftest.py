import pytest


# Globally handle async tests and error on unawaited coroutines
def pytest_collection_modifyitems(session, config, items):
    for item in items:
        item.add_marker(
            pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
        )
        item.add_marker(pytest.mark.filterwarnings("error::RuntimeWarning"))
        item.add_marker(pytest.mark.asyncio)
