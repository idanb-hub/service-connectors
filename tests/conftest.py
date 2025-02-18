import dotenv
import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env():
    _ = dotenv.load_dotenv()
