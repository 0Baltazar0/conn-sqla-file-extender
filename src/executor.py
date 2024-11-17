from types_source import FileFields


class RenameAction(Exception):
    old_key_name: str
    old_key: FileFields
    new_key_name: str
    new_key: FileFields
    file_name: str
    class_name: str

    def __init__(
        self,
        old_key_name: str,
        old_key: FileFields,
        new_key_name: str,
        new_key: FileFields,
        file_name: str,
        class_name: str,
        *args: object,
    ) -> None:
        self.old_key_name = old_key_name
        self.old_key = old_key
        self.new_key_name = new_key_name
        self.new_key = new_key
        self.file_name = file_name
        self.class_name = class_name
        super().__init__(*args)
