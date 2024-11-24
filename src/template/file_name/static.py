import ast
from dataclasses import dataclass

from naming import get_static_file_name_key
from types_source import FileFields
from utils.ast_tools import as_text_replace_content, get_attribute, get_attribute_index


@dataclass
class StaticFileName:
    key_name: str
    key: FileFields
    _class: ast.ClassDef

    def build_file_name_static_value(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.AnnAssign:
        key_name = _key_name or self.key_name
        key = _key or self.key
        return ast.AnnAssign(
            target=ast.Name(get_static_file_name_key(key_name)),
            annotation=ast.Subscript(
                value=ast.Name("Literal"),
                slice=ast.Name(id=key.get("file_name_fix", "")),
            ),
            value=ast.Name(key.get("file_name_fix", "")),
            simple=1,
        )

    def rename_file_name_static(self, key_name: str, key: FileFields) -> None:
        index = get_attribute_index(
            get_static_file_name_key(self.key_name), self._class
        )
        if index is not None:
            new_attribute = self.build_file_name_static_value(key_name, key)
            self._class.body[index] = new_attribute
        else:
            self._class.body.insert(0, self.build_file_name_static_value(key_name, key))

    def purge_file_name_static(self) -> None:
        attribute = get_attribute_index(
            get_static_file_name_key(self.key_name), self._class
        )

        if attribute is not None:
            self._class.body.pop(attribute)

    def build(self) -> None:
        if self.key.get("file_name_fix"):
            attribute = get_attribute(
                get_static_file_name_key(self.key_name), self._class
            )

            if attribute:
                return

            else:
                self._class.body.insert(0, self.build_file_name_static_value())
        else:
            self.purge_file_name_static()

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        self.rename_file_name_static(new_key_name, new_key)

        as_text_replace_content(
            get_static_file_name_key(self.key_name),
            get_static_file_name_key(new_key_name),
            self._class,
        )

    def purge(self) -> None:
        self.purge_file_name_static()
