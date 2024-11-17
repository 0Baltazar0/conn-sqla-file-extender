from typing import TypedDict


class FileFields(TypedDict, total=False):
    mime_type_field_name: str
    mime_type_fix: str
    mime_unhandled: bool
    file_name_field_name: str
    file_name_fix: str
    name_unhandled: bool
    unhandled: bool
