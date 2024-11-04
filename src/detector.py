from typing import Any, Optional, TypedDict

from sqlalchemy import inspect


def must_valid_input(
    question: str, responses: list[str] = ["Y", "n"], case_insensitive: bool = True
) -> str:
    resp = input(f"{question}? [{'/'.join(responses)}]").lower()
    sanitized_responses = [r if not case_insensitive else r.lower() for r in responses]
    while resp not in sanitized_responses:
        resp = input(
            f"Answer not accepted, {question}? [{'/'.join(responses)}]",
        )
        resp = resp if case_insensitive else resp.lower()
    return resp


class FileFields(TypedDict, total=False):
    mime_type_field_name: str
    mime_type_fix: str
    mime_unhandled: bool
    file_name_field_name: str
    file_name_fix: str
    name_unhandled: bool
    unhandled: bool


class ObjectDetector:
    def __init__(self, history: dict[str, Any], base_class: Any) -> None:
        self.history: dict[str, FileFields] = history
        self.keys = [c for c in inspect(base_class).mapper.columns if hasattr(c, "key")]
        self.file_keys = [
            c.key
            for c in self.keys
            if str(c.type.__repr__()).split("(")[0].upper()
            in ["LargeBinary", "BINARY", "BLOB"]
        ]

        self.new_keys = [k for k in self.file_keys if k in history]
        self.missing_keys = [k for k in history if k not in self.file_keys]
        self.renames: list[tuple[str, str, FileFields]] = []

    def rename_mime_type_column_name(
        self, new_name: str, old_name: str, data: FileFields
    ) -> None:
        if data.get("mime_type_field_name"):
            print(f"Old mime type column registered for key {old_name}->{new_name}.")
            if data.get("mime_type_field_name") in [
                k.key.__repr__() for k in self.keys
            ]:
                do_rename_mime_type = (
                    must_valid_input(
                        f"Do you want to rename the mime type field associated with key {new_name}? Old mime type column name {data.get('mime_type_field_name')}?"
                    ).lower()
                    == "y"
                )

    def manage_renamed_keys(self) -> None:
        if not self.renames:
            print("No renames entered")
            return

        print("Executing renames")

        for new_name, old_name, data in self.renames:
            print(f"Managing rename for column {old_name} to {new_name}")

            self.rename_mime_type_column_name(new_name, old_name, data)

    def new_key_mime_type(self, key: str, data: FileFields) -> None:
        if (
            data.get("mime_type_fix")
            or data.get("mime_type_field_name")
            or data.get("mime_unhandled")
        ):
            mime_type_fix = data.get("mime_type_fix")
            mime_type_field_name = data.get("mime_type_field_name")
            mime_unhandled = data.get("mime_unhandled")
            do_reset = must_valid_input(
                "Mime type has been resolved previously, do you want to restart?\n"
                + f"Solution matrix:\n{mime_type_fix=}\n{mime_type_field_name=}\n{mime_unhandled=}"
            )
            if do_reset:
                for key in list(data.keys()):
                    data.pop(key)  # type: ignore
                return self.new_key_mime_type(key, data)
            return

        accounted_mime_fields = [
            kv["mime_type_field_name"]
            for kv in self.history.values()
            if "mime_type_field_name" in kv
        ]
        possible_mime_types = [
            k
            for k in self.keys
            if k not in accounted_mime_fields and "mime" in k.key.lower()
        ]
        if possible_mime_types:
            print("Found some possible mime type keys!")

            do_discover = must_valid_input(
                f"Do you want use discovery to connect this {key} to a mime_type field.",
                ["Y", "n"],
                True,
            )

            if do_discover == "y":
                print(
                    f"What is the {key=}s connected mime type field? Enter X to stop."
                )
                options = [
                    f"Field {sql_key.key} of type {str(sql_key.type.__repr__()).split('(')[0]}. [{i}]"
                    for (sql_key, i) in zip(
                        possible_mime_types, range(len(possible_mime_types))
                    )
                ]
                selection = must_valid_input(
                    "\n".join(options),
                    [str(k) for k in range(len(possible_mime_types))] + ["X"],
                    True,
                )

                if selection.lower() == "x":
                    return self.register_new_key(key)

                data["mime_type_field_name"] = possible_mime_types[int(selection)]
                return
        is_mime_type_fixed = (
            must_valid_input(f"Does this file have a fixed mime type? [{key}]").lower()
            == "y"
        )

        if is_mime_type_fixed:
            fixed_mime_type = input(
                "Please provide a mime type to be used. Hit enter for default (application/octet-stream)"
            )
            fixed_mime_type = (
                fixed_mime_type
                if fixed_mime_type.strip()
                else "application/octet-stream"
            )
            data["mime_type_fix"] = fixed_mime_type
            return

        is_mime_unhandled = (
            must_valid_input(
                f"Do you want to keep mime type unhandled? [{key}]"
            ).lower()
            == "y"
        )
        if is_mime_unhandled:
            data["mime_unhandled"] = True
            return

        do_create = (
            must_valid_input(
                f"Do you want to create a new field for the key [{key}]"
            ).lower()
            == "y"
        )
        if do_create:
            field_name = None

            while not field_name:
                suggestion = input(
                    f"What should be the column name for the mime_type of the column {key}? Hit enter for default ({key}_mime_type)"
                )
                if not suggestion.strip():
                    field_name = f"{key}_mime_type"
                    continue
                else:
                    is_good = (
                        must_valid_input(
                            f"Your answer is {suggestion.strip().replace(' ','_')}. Is this right?"
                        ).lower()
                        == "y"
                    )
                    if is_good:
                        field_name = suggestion.strip().replace(" ", "_")
            else:
                data["mime_type_field_name"] = field_name
                return
        return self.new_key_mime_type(key, data)

    def new_key_file_name(self, key: str, data: FileFields) -> None:
        if (
            data.get("file_name_fix")
            or data.get("file_name_field_name")
            or data.get("name_unhandled")
        ):
            file_name_fix = data.get("file_name_fix")
            file_name_field_name = data.get("file_name_field_name")
            name_unhandled = data.get("name_unhandled")
            do_reset = must_valid_input(
                "File type has been resolved previously, do you want to restart?\n"
                + f"Solution matrix:\n{file_name_fix=}\n{file_name_field_name=}\n{name_unhandled=}"
            )
            if do_reset:
                for key in list(data.keys()):
                    data.pop(key)  # type: ignore
                return self.new_key_file_name(key, data)
            return

        accounted_name_fields = [
            kv["file_name_field_name"]
            for kv in self.history.values()
            if "file_name_field_name" in kv
        ]
        possible_file_names = [
            k
            for k in self.keys
            if k not in accounted_name_fields and "name" in k.key.lower()
        ]
        if possible_file_names:
            print("Found some possible name keys!")

            do_discover = must_valid_input(
                f"Do you want use discovery to connect this {key} to a file_name field.",
                ["Y", "n"],
                True,
            )

            if do_discover == "y":
                print(
                    f"What is the {key=}s connected file name field? Enter X to stop."
                )
                options = [
                    f"Field {sql_key.key} of type {str(sql_key.type.__repr__()).split('(')[0]}. [{i}]"
                    for (sql_key, i) in zip(
                        possible_file_names, range(len(possible_file_names))
                    )
                ]
                selection = must_valid_input(
                    "\n".join(options),
                    [str(k) for k in range(len(possible_file_names))] + ["X"],
                    True,
                )

                if selection.lower() == "x":
                    return self.register_new_key(key)

                data["file_name_field_name"] = possible_file_names[int(selection)]
                return
        is_file_name_fixed = (
            must_valid_input(f"Does this file have a fixed file name? [{key}]").lower()
            == "y"
        )

        if is_file_name_fixed:
            fixed_file_name = input(
                "Please provide a file name to be used. Hit enter for default (application/octet-stream)"
            )
            fixed_file_name = (
                fixed_file_name
                if fixed_file_name.strip()
                else "application/octet-stream"
            )
            data["file_name_fix"] = fixed_file_name
            return

        is_name_unhandled = (
            must_valid_input(
                f"Do you want to keep file name unhandled? [{key}]"
            ).lower()
            == "y"
        )
        if is_name_unhandled:
            data["name_unhandled"] = True
            return

        do_create = (
            must_valid_input(
                f"Do you want to create a new field for the key [{key}] as file name"
            ).lower()
            == "y"
        )
        if do_create:
            field_name = None

            while not field_name:
                suggestion = input(
                    f"What should be the column name for the file_name of the column {key}? Hit enter for default ({key}_file_name)"
                )
                if not suggestion.strip():
                    field_name = f"{key}_file_name"
                    continue
                else:
                    is_good = (
                        must_valid_input(
                            f"Your answer is {suggestion.strip().replace(' ','_')}. Is this right?"
                        ).lower()
                        == "y"
                    )
                    if is_good:
                        field_name = suggestion.strip().replace(" ", "_")
            else:
                data["file_name_field_name"] = field_name
                return
        return self.new_key_file_name(key, data)

    def register_new_key(self, key: str) -> None:
        print("Registering new key: %s", key)

        data: FileFields = self.history.get(key, {})
        self.history[key] = data

        keep_unhandled = (
            must_valid_input(f"Do you want to keep the key [{key}] unhandled?").lower()
            == "y"
        )
        if keep_unhandled:
            data["unhandled"] = True
            return

        if (
            not data.get("mime_type_field_name")
            and not data.get("mime_type_fix")
            and not data.get("mime_unhandled")
        ):
            self.new_key_mime_type(key, data)
        if (
            not data.get("file_name_field_name")
            and not data.get("file_name_fix")
            and not data.get("name_unhandled")
        ):
            self.new_key_file_name(key, data)

    def address_new_keys(self) -> None:
        # The source will change during operation
        start_keys = [k for k in self.new_keys]
        for key in start_keys:
            print("A new key has been detected: %s", key)
            is_rename = (
                must_valid_input("Is this a rename of a new field?", ["Y", "n"], True)
                == "y"
            )

            if is_rename:
                print(f"What is the {key=} renamed from? Enter X to stop.")
                options = [
                    f"Is it renamed from {missing_key}? Select [{i}]."
                    for (missing_key, i) in zip(
                        self.missing_keys, range(len(self.missing_keys))
                    )
                ]
                selection = must_valid_input(
                    "\n".join(options),
                    [str(i) for i in range(len(self.missing_keys))] + ["X"],
                    True,
                )
                if selection == "x":
                    break
                else:
                    self.renames.append(
                        (
                            key,
                            self.missing_keys[int(selection)],
                            self.history[self.missing_keys[int(selection)]],
                        )
                    )
                    self.new_keys.pop(self.new_keys.index(key))
                    continue

            print("New key identified: %s", key)
            self.register_new_key(key)

        else:
            return
        self.address_new_keys()
