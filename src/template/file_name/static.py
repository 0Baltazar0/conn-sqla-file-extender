import ast
from dataclasses import dataclass

from naming import get_static_mime_key
from types_source import FileFields
from utils.ast_tools import get_attribute, get_attribute_index


@dataclass
class StaticMimeType:
    key_name: str
    key: FileFields
    _class: ast.ClassDef

    def build_mime_static_value(
        self, _key_name: str | None = None, _key: FileFields | None = None
    ) -> ast.AnnAssign:
        key_name = _key_name or self.key_name
        key = _key or self.key
        return ast.AnnAssign(
            target=ast.Name(get_static_mime_key(key_name)),
            annotation=ast.Subscript(
                value=ast.Name("Literal"),
                slice=ast.Name(id=key.get("mime_type_fix", "")),
            ),
            value=ast.Name(key.get("mime_type_fix", "")),
            simple=1,
        )

    def rename_mime_static(self, key_name: str, key: FileFields) -> None:
        index = get_attribute_index(get_static_mime_key(self.key_name), self._class)
        if index is not None:
            new_attribute = self.build_mime_static_value(key_name, key)
            self._class.body[index] = new_attribute
        else:
            self._class.body.insert(0, self.build_mime_static_value(key_name, key))

    def purge_mime_static(self) -> None:
        attribute = get_attribute_index(get_static_mime_key(self.key_name), self._class)

        if attribute is not None:
            self._class.body.pop(attribute)

    def build(self) -> None:
        if self.key.get("mime_type_fix"):
            attribute = get_attribute(get_static_mime_key(self.key_name), self._class)

            if attribute:
                return

            else:
                self._class.body.insert(0, self.build_mime_static_value())
        else:
            self.purge_mime_static()

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        if new_key.get("mime_type_fix"):
            self.rename_mime_static(new_key_name, new_key)
        else:
            self.purge_mime_static()

    def purge(self) -> None:
        self.purge_mime_static()
