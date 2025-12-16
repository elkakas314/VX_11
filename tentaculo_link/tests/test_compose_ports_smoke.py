from config.settings import settings


def test_tentaculo_link_port_in_compose():
    with open("docker-compose.yml", "r") as f:
        docker = f.read()
    expected = f'"{settings.tentaculo_link_port}:{settings.tentaculo_link_port}"'
    # Allow either quoted or unquoted mapping
    assert (
        f"{settings.tentaculo_link_port}:{settings.tentaculo_link_port}" in docker
    ), "Compose does not map tentaculo_link port to settings"
