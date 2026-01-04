from typing import Generator, Optional


def get_db() -> Generator[Optional[object], None, None]:
    # TODO: provide a real database session once persistence is defined.
    yield None
