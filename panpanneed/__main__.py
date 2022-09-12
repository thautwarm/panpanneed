from wisepy2 import wise
from panpanneed import start_server


def CLI(*, rootdir=".", port: int = 6752):
    start_server(port, rootdir)


if __name__ == "__main__":
    wise(CLI)()
