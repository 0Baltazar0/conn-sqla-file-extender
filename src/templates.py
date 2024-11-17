import ast

from naming import (
    get_column_file_name_key,
    get_column_mime_key,
    get_file_variable,
    get_mime_variable_name,
    get_static_file_name_key,
    get_static_mime_key,
    starlette_get_name,
    werkzeug_get_name,
)
from types_source import FileFields


def property_werkzeug_getter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = f"self.{get_mime_variable_name(key,key_name)}" or "None"
    file_name = f"self.{get_file_variable(key,key_name)}" or "None"
    template = f"""
@property
def {werkzeug_get_name(key_name)}(self)->flask.Response:
    mime_type = {mime_key}
    file_name = {file_name}
    return flask.send_file(self.{key_name},attachment_filename={file_name},mimetype={mime_key})
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def property_werkzeug_setter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = (
        f"self.{get_mime_variable_name(key,key_name)}"
        if key.get("mime_type_field_name")
        else None
    )
    file_name = (
        f"self.{get_file_variable(key,key_name)}"
        if key.get("file_name_field_name")
        else None
    )
    template = f"""
@{werkzeug_get_name(key_name)}.setter
def {werkzeug_get_name(key_name)}(self,file:werkzeug.FileStorage)->None:
    mime_type = file.mimetype
    file_name = file.filename
    data = file.read()
    self.{key} = data
    {('self.'+mime_key+' = mime_type') if mime_key else ''}
    {('self.'+file_name+' = file_name') if file_name else ''}
    
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def property_starlette_getter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = f"self.{get_mime_variable_name(key,key_name)}" or "None"
    file_name = f"self.{get_file_variable(key,key_name)}" or "None"
    template = f"""
@property
async def {starlette_get_name(key_name)}(self)->starlette.responses.FileResponse:
    mime_type = {mime_key}
    file_name = {file_name}
    return starlette.responses.FileResponse(
        self.{key_name},
        filename=file_name,
        media_type=mime_type
    )
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def property_starlette_setter_template(
    key_name: str, key: FileFields
) -> ast.FunctionDef:
    mime_key = (
        f"self.{get_mime_variable_name(key,key_name)}"
        if key.get("mime_type_field_name")
        else None
    )
    file_name = (
        f"self.{get_file_variable(key,key_name)}"
        if key.get("file_name_field_name")
        else None
    )
    template = f"""
@{starlette_get_name(key_name)}.setter
async def {starlette_get_name(key_name)}(self,file:starlette.datastructures.UploadFile)->None:
    mime_type = file.content_type
    file_name = file.filename
    data = await file.read()
    self.{key} = data
    {('self.'+mime_key+' = mime_type') if mime_key else ''}
    {('self.'+file_name+' = file_name') if file_name else ''}
    
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_column_template(column_name: str) -> ast.AnnAssign:
    template = f"{get_column_mime_key(column_name)}:Mapped[str] = String('{get_column_mime_key(column_name)}')"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def mime_type_getter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@property
def {get_column_mime_key(key_name)}(self)->str:
    return self.{column_name}
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_setter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@{get_column_mime_key(key_name)}.setter
def {get_column_mime_key(key_name)}(self,value:str)->None:
    self.{column_name} = value
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def mime_type_static_template(key_name: str, static_mime: str) -> ast.AnnAssign:
    template = (
        f"{get_static_mime_key(key_name)}:Literal['{static_mime}'] = '{static_mime}'"
    )

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_type_column_template(property_name: str) -> ast.AnnAssign:
    template = f"{get_column_file_name_key(property_name)}:Mapped[str] = String('{get_column_file_name_key(property_name)}')"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_name_static_template(key_name: str, static_name: str) -> ast.AnnAssign:
    template = f"{get_static_file_name_key(key_name)}:Literal['{static_name}'] = '{static_name}'"

    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.AnnAssign):
        raise Exception(f"Somehow this is not a Assign {type(fun)}")

    return fun


def file_name_getter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@property
def {get_column_file_name_key(key_name)}(self)->str:
    return self.{column_name}
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun


def file_name_setter_template(key_name: str, column_name: str) -> ast.FunctionDef:
    template = f"""@{get_column_file_name_key(key_name)}.setter
def {get_column_file_name_key(key_name)}(self,value:str)->None:
    self.{column_name} = value
"""
    fun = ast.parse(template).body[0]

    if not isinstance(fun, ast.FunctionDef):
        raise Exception(f"Somehow this is not a function {type(fun)}")

    return fun
