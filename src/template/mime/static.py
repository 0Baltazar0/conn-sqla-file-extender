import ast
from dataclasses import dataclass

from naming import get_static_mime_key
from templates import TemplateException
from types_source import FileFields
from utils.ast_tools import (
    as_text_replace_content,
    get_attribute,
    get_attribute_index,
    pr,
)


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
        mime_type = key.get("mime_type_fix")

        if not mime_type:
            raise TemplateException("")
        return ast.AnnAssign(
            target=ast.Name(get_static_mime_key(key_name)),
            annotation=ast.Subscript(
                value=ast.Name("Literal"),
                slice=ast.Name(id=mime_type),
            ),
            value=ast.Name(mime_type),
            simple=1,
        )

    def rename_mime_static(self, key_name: str, key: FileFields) -> None:
        index = get_attribute_index(get_static_mime_key(self.key_name), self._class)
        pr(self._class)
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
        attribute = get_attribute(get_static_mime_key(self.key_name), self._class)

        if attribute:
            return

        else:
            self._class.body.insert(0, self.build_mime_static_value())

    def change(self, new_key_name: str, new_key: FileFields) -> None:
        self.rename_mime_static(new_key_name, new_key)
        as_text_replace_content(
            get_static_mime_key(self.key_name),
            get_static_mime_key(new_key_name),
            self._class,
        )

    def purge(self) -> None:
        self.purge_mime_static()
