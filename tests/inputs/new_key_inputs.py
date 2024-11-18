def new_key_start(un_handle: bool) -> list[str]:
    if un_handle:
        return ["n", "y"]
    return ["n", "n"]


def new_key_rename(index: int = 0) -> list[str]:
    return ["y", str(index)]


def rename_keep_unhandled(do: bool) -> list[str]:
    return ["y" if do else "n"]
