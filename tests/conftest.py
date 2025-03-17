import os
import pytest

@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    original_db = os.environ.get("POSTGRES_DB")
    os.environ["POSTGRES_DB"] = "test_wecom"
    yield
    if original_db is not None:
        os.environ["POSTGRES_DB"] = original_db
    else:
        del os.environ["POSTGRES_DB"]