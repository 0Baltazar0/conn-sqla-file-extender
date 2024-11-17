import importlib.util
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Any, Literal, TypedDict

from sqlalchemy import inspect
from yaml import Loader, load

from executor import (
    ApplyHistoryAction,
    NewKeyAction,
    ReAddHistoryAction,
    RemoveHistoryCleanAction,
    RemoveHistoryKeyAsIsAction,
    RenameAction,
)
from types_source import FileFields
from utils.io import must_valid_from_list, must_valid_input


class StartupException(Exception):
    pass


class UnexpectedCodeSegment(Exception):
    def __init__(self, segment: str, *args: object) -> None:
        self.segment = segment
        super().__init__(*args)


class AbortException(Exception):
    pass


class RenameData(TypedDict):
    old_key_name: str
    new_key_name: str
    old_key: FileFields
    new_key: FileFields


BINARY_FIELDS = ["LargeBinary", "BINARY", "BLOB"]

STRING_FIELDS = [
    "String",
    "Text",
    "NCHAR",
    "NVARCHAR",
    "VARCHAR",
    "Unicode",
    "UnicodeText",
]


class Runtime:
    history: dict[str, FileFields]
    spec: ModuleSpec | None
    module: ModuleType
    _class_object: Any
    all_keys: list[Any]

    def __init__(self, file_name: str, history_path: str, class_name: str) -> None:
        self.file_name = file_name
        self.history_path = history_path
        self.class_name = class_name

    def load_history(self) -> None:
        with open(self.history_path) as in_file:
            self.history = load(in_file, Loader).get(self.class_name, {})

    def load_module(self) -> None:
        self.spec = importlib.util.spec_from_file_location(
            self.file_name, self.file_name
        )
        if self.spec and self.spec.loader:
            self.module = importlib.util.module_from_spec(self.spec)
            self.spec.loader.exec_module(self.module)
            self._class_object = getattr(self.module, self.class_name)
        else:
            raise StartupException("Couldn't load the target module.")

    def find_keys(self) -> None:
        self.keys = [
            c for c in inspect(self._class_object).mapper.columns if hasattr(c, "key")
        ]
        self.file_keys = [
            c.key
            for c in self.keys
            if str(c.type.__repr__()).split("(")[0].upper() in BINARY_FIELDS
        ]

    def find_new_keys(self) -> None:
        self.new_keys = [k for k in self.file_keys if k in self.history]

    def resolve_new_mime_static(self, new_key_name) -> FileFields:
        static_mime_value = input(
            f"Provide static mime type for '{new_key_name}', press enter to select default [application/octet-stream]:"
        )

        static_mime_value = (
            static_mime_value if static_mime_value else "application/octet-stream"
        )

        return {"mime_type_fix": static_mime_value}

    def resolve_new_file_name_static(self, new_key_name) -> FileFields:
        static_file_name_value = input(
            f"Provide static file name for '{new_key_name}', press enter to select default [binary.file]:"
        )

        static_file_name_value = (
            static_file_name_value if static_file_name_value else "binary.file"
        )

        return {"file_name_fix": static_file_name_value}

    def resolve_new_mime_dynamic_select(self, new_key_name: str) -> FileFields:
        possible_keys = [
            c.key
            for c in self.keys
            if str(c.type.__repr__()).split("(")[0].upper() in STRING_FIELDS
        ]

        if not possible_keys:
            raise AbortException("No keys available for selection.")

        selected_key = must_valid_from_list(
            f"Which one of these keys do you want to associate with the mime type of '{new_key_name}'?",
            "Column %s",
            possible_keys,
        )
        if selected_key == "x":
            raise AbortException("New mime type key selection aborted.")
        return {"mime_type_field_name": selected_key}

    def resolve_new_file_name_dynamic_select(self, new_key_name: str) -> FileFields:
        possible_keys = [
            c.key
            for c in self.keys
            if str(c.type.__repr__()).split("(")[0].upper() in STRING_FIELDS
        ]

        if not possible_keys:
            raise AbortException("No keys available for selection.")

        selected_key = must_valid_from_list(
            f"Which one of these keys do you want to associate with the file name of '{new_key_name}'?",
            "Column %s",
            possible_keys,
        )
        if selected_key == "x":
            raise AbortException("New file name key selection aborted.")
        return {"file_name_field_name": selected_key}

    def resolve_new_mime_dynamic_add(self, new_key_name: str) -> FileFields:
        new_key_name = input(
            f"Create a new column to hold mime type for the key '{new_key_name}'.Press enter to use default [{new_key_name}_mime_col:String]. Press x to abort."
        )

        if new_key_name.lower() == "x":
            raise AbortException("New mime type key creating aborted.")

        new_key_name = new_key_name if new_key_name else f"{new_key_name}_mime_col"

        return {"mime_type_field_name": new_key_name}

    def resolve_new_file_name_dynamic_add(self, new_key_name: str) -> FileFields:
        new_key_name = input(
            f"Create a new column to hold file name for the key '{new_key_name}'.Press enter to use default [{new_key_name}_file_name_col:String]. Press x to abort."
        )

        if new_key_name.lower() == "x":
            raise AbortException("New file name key creating aborted.")

        new_key_name = new_key_name if new_key_name else f"{new_key_name}_file_name_col"

        return {"file_name_field_name": new_key_name}

    def resolve_new_mime_dynamic(self, new_key_name: str) -> FileFields:
        run_selector = must_valid_input(
            f"Do you want to select an existing database field for '{new_key_name}'?"
        )

        if run_selector:
            return self.resolve_new_mime_dynamic_select(new_key_name)

        return self.resolve_new_mime_dynamic_add(new_key_name)

    def resolve_new_file_name_dynamic(self, new_key_name: str) -> FileFields:
        run_selector = must_valid_input(
            f"Do you want to select an existing database field as file name for '{new_key_name}'?"
        )

        if run_selector:
            return self.resolve_new_file_name_dynamic_select(new_key_name)

        return self.resolve_new_file_name_dynamic_add(new_key_name)

    def resolve_new_mime(self, new_key_name: str) -> FileFields:
        new_mime_select = must_valid_input(
            f"Resolving mime type for key '{new_key_name}'. How should the mime type be resolved?\n <Static> has a fixed static mime type,\n <Dynamic> has a reference to another field in the database,\n <Unhandled> means no further action.\n Press X to abort.",
            ["static", "dynamic", "unhandled", "x"],
        ).lower()

        if new_mime_select == "x":
            raise AbortException("New mime type selection aborted")

        if new_mime_select == "unhandled":
            return {"mime_unhandled": True}

        if new_mime_select == "static":
            return self.resolve_new_mime_static(new_key_name)

        if new_key_name == "dynamic":
            return self.resolve_new_mime_dynamic(new_key_name)

        raise Exception(
            f"Unexpected response in resolving mime type, {new_mime_select}"
        )

    def resolve_new_file_name(self, new_key_name: str) -> FileFields:
        new_file_name_select = must_valid_input(
            f"Resolving file name for key '{new_key_name}'. How should the file name be resolved?\n <Static> has a fixed static file name,\n <Dynamic> has a reference to another field in the database,\n <Unhandled> means no further action.\n Press X to abort.",
            ["static", "dynamic", "unhandled", "x"],
        ).lower()

        if new_file_name_select == "x":
            raise AbortException("New file name selection aborted")

        if new_file_name_select == "unhandled":
            return {"name_unhandled": True}

        if new_file_name_select == "static":
            return self.resolve_new_file_name_static(new_key_name)

        if new_key_name == "dynamic":
            return self.resolve_new_file_name_dynamic(new_key_name)

        raise Exception(
            f"Unexpected response in resolving file_name, {new_file_name_select}"
        )

    def resolve_rename_mime(self, new_key_name: str, old_key: FileFields) -> FileFields:
        is_old_static = old_key.get("mime_type_fix")
        if is_old_static:
            keep_old_static = (
                must_valid_input(
                    f"Original key '{new_key_name}' is a static mime type  <{is_old_static}>, do you want to keep it?"
                ).lower()
                == "y"
            )

            if keep_old_static:
                return {"mime_type_fix": is_old_static}
        is_old_dynamic = old_key.get("mime_type_field_name")
        if is_old_dynamic:
            keep_old_dynamic = (
                must_valid_input(
                    f"Original key '{new_key_name}' is a dynamic mime type, referencing column <{is_old_dynamic}>, do you want to keep it?"
                ).lower()
                == "y"
            )

            if keep_old_dynamic:
                return {"mime_type_field_name": is_old_dynamic}

        is_old_unhandled = old_key.get("mime_unhandled")

        if is_old_unhandled:
            keep_unhandled = must_valid_input(
                f"Original key '{new_key_name}' has unhandled mime type, do you want to keep it?"
            )

            if keep_unhandled:
                return {"mime_unhandled": True}

        return self.resolve_new_mime(new_key_name)

    def resolve_rename_file_name(
        self, new_key_name: str, old_key: FileFields
    ) -> FileFields:
        is_old_static = old_key.get("file_name_fix")
        if is_old_static:
            keep_old_static = (
                must_valid_input(
                    f"Original key '{new_key_name}' has a static file name  <{is_old_static}>, do you want to keep it?"
                ).lower()
                == "y"
            )

            if keep_old_static:
                return {"file_name_fix": is_old_static}
        is_old_dynamic = old_key.get("file_name_field_name")
        if is_old_dynamic:
            keep_old_dynamic = (
                must_valid_input(
                    f"Original key '{new_key_name}' has a dynamic file name, referencing column <{is_old_dynamic}>, do you want to keep it?"
                ).lower()
                == "y"
            )

            if keep_old_dynamic:
                return {"file_name_field_name": is_old_dynamic}

        is_old_unhandled = old_key.get("name_unhandled")

        if is_old_unhandled:
            keep_unhandled = must_valid_input(
                f"Original key '{new_key_name}' has unhandled file name, do you want to keep it?"
            )

            if keep_unhandled:
                return {"name_unhandled": True}

        return self.resolve_new_file_name(new_key_name)

    def resolve_rename_build_new_key(
        self, new_key_name: str, old_key_name: str, old_key: FileFields
    ) -> None:
        new_key: FileFields = {}

        if old_key.get("unhandled"):
            keep_unhandled = must_valid_input(
                "The old key is set as unhandled. Do you want to keep it unhandled?"
            )
            if keep_unhandled:
                new_key = {"unhandled": True}
        else:
            new_key.update(self.resolve_rename_mime(new_key_name, old_key))
            new_key.update(self.resolve_rename_file_name(new_key_name, old_key))

        raise RenameAction(
            old_key_name,
            old_key,
            new_key_name,
            new_key,
            self.file_name,
            self.class_name,
            self.history_path,
        )

    def resolve_rename(self, key_name: str) -> None:
        missing_keys = [k for k in self.history if k not in self.file_keys]

        missing_key_question = [
            f"Select which key is '{key_name}' renamed from. Press x to abort"
        ] + [f"{k}, [{i}]" for k, i in zip(missing_keys, range(len(missing_keys)))]

        which_key = must_valid_input(
            "\n".join(missing_key_question),
            ["x"] + [str(i) for i in range(len(missing_keys))],
        ).lower()
        if which_key == "x":
            raise AbortException("Rename was aborted.")

        rename_source_name = missing_keys[int(which_key)]

        self.resolve_rename_build_new_key(
            key_name, rename_source_name, self.history[rename_source_name]
        )

    def resolve_add_new_key(self, new_key_name: str) -> None:
        is_unhandled = (
            must_valid_input(f"Do you want to keep '{new_key_name}' unhandled?").lower()
            == "y"
        )
        if is_unhandled:
            raise NewKeyAction(
                new_key_name,
                {"unhandled": True},
                self.file_name,
                self.class_name,
                self.history_path,
            )

        new_key: FileFields = {}

        new_key.update(self.resolve_new_mime(new_key_name))
        new_key.update(self.resolve_new_file_name(new_key_name))

        raise NewKeyAction(
            new_key_name,
            new_key,
            self.file_name,
            self.class_name,
            self.history_path,
        )

    def resolve_new_key(self, new_key_name: str) -> None:
        is_rename = (
            must_valid_input(
                f"New key found '{new_key_name}'. Is this a rename"
            ).lower()
            == "y"
        )
        if is_rename:
            self.resolve_rename(new_key_name)
        else:
            self.resolve_add_new_key(new_key_name)

    def has_new_keys(self) -> Literal[False]:
        new_key_name = next((k for k in self.file_keys if k not in self.history), None)
        if new_key_name:
            self.resolve_new_key(new_key_name)
            raise UnexpectedCodeSegment("new-key-no-reaction")
        return False

    def resolve_missing_key(self, old_key_name: str, old_key: FileFields) -> None:
        un_handle = must_valid_input(
            f"A previous key '{old_key_name}' is missing from the class.\nDo you want to reinstate it <readd>,\nPurge it <clean>, Remove it without any action <as_is>?",
            ["re_add", "clean", "as_is"],
        )
        if un_handle == "as_is":
            raise RemoveHistoryKeyAsIsAction(
                self.file_name, old_key_name, self.class_name, self.history_path
            )
        if un_handle == "clean":
            raise RemoveHistoryCleanAction(
                self.file_name,
                old_key_name,
                old_key,
                self.class_name,
                self.history_path,
            )
        if un_handle == "re_add":
            raise ReAddHistoryAction(
                self.file_name,
                old_key_name,
                old_key,
                self.class_name,
                self.history_path,
            )
        raise UnexpectedCodeSegment("resolve-missing-key-no-solution")

    def has_missing_keys(self) -> Literal[False]:
        missing_key = next((k for k in self.history if k not in self.file_keys), None)
        if missing_key:
            raise UnexpectedCodeSegment("missing-key-no-reaction")
        return False

    def execute(self) -> None:
        self.has_new_keys()
        self.has_missing_keys()
        raise ApplyHistoryAction(self.file_name, self.class_name, self.history)
