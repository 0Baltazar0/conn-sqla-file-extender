import ast
from typing import TypeAlias
from ast_comments import parse, unparse

WalkableClasses: TypeAlias = (
    ast.Module
    | ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.For
    | ast.AsyncFor
    | ast.While
    | ast.If
    | ast.With
    | ast.AsyncWith
    | ast.Try
    | ast.TryStar
    | ast.ExceptHandler
    | ast.match_case
)


def is_property(fun: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    has_property_decorator = next(
        (
            dec
            for dec in fun.decorator_list
            if isinstance(dec, ast.Name) and dec.id == "property"
        ),
        None,
    )
    return has_property_decorator is not None


def as_text_replace_content(
    old_var: str,
    new_var: str,
    _obj: WalkableClasses,
) -> None:
    """Simple replace in a stringified code segment
        This does not manage any similarly named variables, avoid using those in the class

    Args:
        old_var (str): The string of the old variable
        new_var (str): The string of the new_variable
        _class (ast.ClassDef): The class containing the file key
    """
    as_text = unparse(_obj)

    as_text.replace(old_var, new_var)
    as_ast: ast.Module = parse(as_text)  # type: ignore
    _obj.body = as_ast.body
    return


def rename_property_key_reference(
    property_name: str, old_reference: str, new_reference: str, _class: ast.ClassDef
) -> None:
    getter = get_property_getter(property_name, _class)
    if getter:
        as_text_replace_content(old_reference, new_reference, getter)
    setter = get_property_setter(property_name, _class)
    if setter:
        as_text_replace_content(old_reference, new_reference, setter)
    return


def rename_decorator_setter(
    old_name: str, new_name: str, decorators: list[ast.expr]
) -> None:
    for dec in decorators:
        if (
            isinstance(dec, ast.Attribute)
            and dec.attr == "setter"
            and isinstance(dec.value, ast.Name)
            and dec.value.id == old_name
        ):
            dec.value.id = new_name


def rename_property_key_name(
    old_property_name: str, new_property_name: str, _class: ast.ClassDef
) -> None:
    getter = get_property_getter(old_property_name, _class)
    if getter:
        getter.name = new_property_name
    setter = get_property_setter(old_property_name, _class)
    if setter:
        setter.name = new_property_name
        rename_decorator_setter(
            old_property_name, new_property_name, setter.decorator_list
        )
    return


def is_property_setter(
    fun: ast.FunctionDef | ast.AsyncFunctionDef, property_name: str
) -> bool:
    has_property_decorator = next(
        (
            dec
            for dec in fun.decorator_list
            if isinstance(dec, ast.Attribute)
            and dec.attr == "setter"
            and isinstance(dec.value, ast.Name)
            and dec.value.id == property_name
        ),
        None,
    )
    return has_property_decorator is not None


def get_property_setter(
    property_name: str, _class: ast.ClassDef
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    return next(
        (
            fn
            for fn in _class.body
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
            and fn.name == property_name
            and is_property_setter(fn, property_name)
        ),
        None,
    )


def get_property_getter(
    property_name: str, _class: ast.ClassDef
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    return next(
        (
            fn
            for fn in _class.body
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
            and fn.name == property_name
            and is_property(fn)
        ),
        None,
    )


def turn_property_to_attribute(
    property_name: str, attribute_: ast.AnnAssign, _class: ast.ClassDef
) -> None:
    property_getter = next(
        (
            fn
            for fn in _class.body
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
            and fn.name == property_name
            and is_property(fn)
        ),
        None,
    )
    property_setter = next(
        (
            fn
            for fn in _class.body
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
            and fn.name == property_name
            and is_property_setter(fn, property_name)
        ),
        None,
    )
    index_element = property_getter or property_setter
    _class.body.insert(
        _class.body.index(index_element) if index_element else 0,
        attribute_,
    )
    if property_getter:
        _class.body.remove(property_getter)
    if property_setter:
        _class.body.remove(property_setter)
    return


def purge_attribute(attribute_name: str, _class: WalkableClasses) -> None:
    attribute = next(
        (
            atr
            for atr in _class.body
            if isinstance(atr, ast.AnnAssign)
            and isinstance(atr.target, ast.Name)
            and atr.target.id == attribute_name
        ),
        None,
    )
    if attribute:
        _class.body.remove(attribute)

    return


def purge_property(property_name: str, _class: ast.ClassDef) -> None:
    getter = get_property_getter(property_name, _class)
    setter = get_property_setter(property_name, _class)
    if getter:
        _class.body.remove(getter)
    if setter:
        _class.body.remove(setter)
    return


def add_properties_if_not_exist(
    property_name: str,
    setter: ast.FunctionDef | ast.AsyncFunctionDef,
    getter: ast.FunctionDef | ast.AsyncFunctionDef,
    _class: ast.ClassDef,
    preferred_index: int = 0,
) -> None:
    has_getter = get_property_getter(property_name, _class)

    has_setter = get_property_setter(property_name, _class)
    if not has_setter:
        setter_index = _class.body.index(has_getter) if has_getter else preferred_index
        _class.body.insert(setter_index, setter)
    if not has_getter:
        _class.body.insert(preferred_index, getter)
    return


def add_attribute_if_not_exists(
    attribute_name: str,
    attribute_: ast.AnnAssign,
    _class: WalkableClasses,
    preferred_index: int = 0,
) -> None:
    has_attr = get_attribute(attribute_name, _class)
    if has_attr:
        switch_attributes(attribute_name, attribute_, _class)
    else:
        _class.body.insert(preferred_index, attribute_)


def get_attribute_index(attribute_name: str, _class: ast.ClassDef) -> int | None:
    atr = get_attribute(attribute_name, _class)
    if atr:
        return _class.body.index(atr)
    return None


def switch_attributes(
    attribute_name: str, attribute_: ast.AnnAssign, _class: WalkableClasses
) -> None:
    attribute = next(
        (
            atr
            for atr in _class.body
            if isinstance(atr, ast.AnnAssign)
            and isinstance(atr.target, ast.Name)
            and atr.target.id == attribute_name
        ),
        None,
    )
    index = _class.body.index(attribute) if attribute else 0
    _class.body.insert(index, attribute_)
    if attribute:
        _class.body.remove(attribute)
    return


def turn_attribute_into_property(
    attribute_name: str,
    getter: ast.FunctionDef | ast.AsyncFunctionDef | None,
    setter: ast.AsyncFunctionDef | ast.FunctionDef | None,
    _class: WalkableClasses,
) -> None:
    attribute = next(
        (
            atr
            for atr in _class.body
            if isinstance(atr, ast.AnnAssign)
            and isinstance(atr.target, ast.Name)
            and atr.target.id == attribute_name
        ),
        None,
    )

    index = _class.body.index(attribute) if attribute else 0

    if setter:
        _class.body.insert(index, setter)
    if getter:
        _class.body.insert(index, getter)
    if attribute:
        _class.body.remove(attribute)


def get_attribute(attribute_name: str, _class: WalkableClasses) -> ast.AnnAssign | None:
    return next(
        (
            atr
            for atr in _class.body
            if isinstance(atr, ast.AnnAssign)
            and isinstance(atr.target, ast.Name)
            and atr.target.id == attribute_name
        ),
        None,
    )


def get_assign(
    assign_name: str, _class: WalkableClasses, single_target=False
) -> ast.Assign | None:
    return next(
        (
            atr
            for atr in _class.body
            if isinstance(atr, ast.Assign)
            and any(
                (
                    isinstance(target, ast.Name) and target.id == assign_name
                    for target in atr.targets
                )
            )
            and (single_target is False or len(atr.targets) == 1)
        ),
        None,
    )


def get_class(class_name: str, module: WalkableClasses) -> ast.ClassDef | None:
    return next(
        (
            atr
            for atr in module.body
            if isinstance(atr, ast.ClassDef) and atr.name == class_name
        ),
        None,
    )


def get_function(
    function_name: str,
    module: WalkableClasses,
) -> ast.FunctionDef | None:
    _module: ast.Module = module  # type: ignore
    return next(
        (
            atr
            for atr in _module.body
            if isinstance(atr, ast.FunctionDef) and atr.name == function_name
        ),
        None,
    )


def get_ann_or_assign(
    value_name: str, module: WalkableClasses, single_target: bool = False
) -> ast.AnnAssign | ast.Assign | None:
    as_annassign = get_attribute(value_name, module)
    if as_annassign:
        return as_annassign

    as_assign = get_assign(value_name, module, single_target)
    return as_assign
