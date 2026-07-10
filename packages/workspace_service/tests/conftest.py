from data_vault import install_default_secret_provider


def pytest_configure() -> None:
    install_default_secret_provider()
