from types_source import FileFields


def get_static_mime_key(key_name: str) -> str:
    return key_name + "static_mime_type"


def get_column_mime_key(key_name: str) -> str:
    return key_name + "_mime_type"


def get_static_file_name_key(key_name: str) -> str:
    return key_name + "static_file_name"


def get_column_file_name_key(key_name: str) -> str:
    return key_name + "_file_name"


def get_mime_variable_name(key: FileFields, key_name: str) -> str | None:
    if key.get("mime_unhandled"):
        return None
    elif key.get("mime_type_field_name"):
        return get_column_mime_key(key_name)
    else:
        return get_static_mime_key(key_name)


def get_file_variable(key: FileFields, key_name: str) -> str | None:
    if key.get("name_unhandled"):
        return None
    elif key.get("file_name_field_name"):
        return key.get("file_name_field_name")
    else:
        return get_static_file_name_key(key_name)


def werkzeug_get_name(key_name: str) -> str:
    return f"{key_name}_flask"


def starlette_get_name(key_name: str) -> str:
    return f"{key_name}_asyncio"
