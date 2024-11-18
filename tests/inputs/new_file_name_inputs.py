from typing import Literal


def get_file_name_input(
    mode: Literal["static"] | Literal["dynamic"] | Literal["unhandled"],
    value: str | None = None,
    index: int | None = None,
) -> list[str]:
    if value is not None:
        if index is not None:
            raise Exception("Can't use both value and index")
    match mode:
        case "dynamic":
            if index is not None:
                return ["dynamic", "y", str(index)]
            if value is not None:
                return ["dynamic", "n", value]

            return ["dynamic", "n", ""]
        case "static":
            if not value:
                return ["static", ""]
            return ["static", value]
        case "unhandled":
            return ["unhandled"]
