from app.main import create_server_config


def test_server_binds_to_loopback_only() -> None:
    server_socket = create_server_config(port=0).bind_socket()
    try:
        assert server_socket.getsockname()[0] == "127.0.0.1"
    finally:
        server_socket.close()
