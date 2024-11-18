from typing import Literal


def get_missing_key_input(
    resolution: Literal["re_add"] | Literal["clean"] | Literal["as_is"],
) -> list[str]:
    return [resolution]
