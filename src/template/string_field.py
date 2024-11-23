import ast
from dataclasses import dataclass

from utils.ast_tools import get_ann_or_assign

"""Holds and manages the format
{field_name}:Mapped[str] = String({field_name})
"""


@dataclass
class GenericStringDatabaseEntry:
    field_name: str
    _class: ast.ClassDef

    def build_row(self, _field_name: str | None = None) -> ast.AnnAssign:
        field_name = _field_name or self.field_name
        ann = ast.Subscript(slice=ast.Name(id="str"), value=ast.Name(id="Mapped"))
        target = ast.Name(id=field_name)
        value = ast.Call(
            func=ast.Name(id="String"), args=[ast.Name(id=field_name)], keywords=[]
        )
        return ast.AnnAssign(target=target, annotation=ann, value=value, simple=1)

    def rename_row(self, new_key_name: str) -> None:
        attribute = get_ann_or_assign(self.field_name, self._class, True)
        if not attribute:
            self._class.body.insert(0, self.build_row(new_key_name))
        else:
            if isinstance(attribute, ast.AnnAssign):
                attribute.target = ast.Name(id=new_key_name)
            else:
                attribute.targets[0] = ast.Name(new_key_name)
