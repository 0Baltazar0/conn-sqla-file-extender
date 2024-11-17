from typing import TypeAlias
from yaml import dump, parse
from execute.apply_history import apply_history
from execute.purge import purge
from execute.rename import rename
from logger import LOGGER
from types_source import FileFields


class RenameAction(Exception):
    old_key_name: str
    old_key: FileFields
    new_key_name: str
    new_key: FileFields
    file_name: str
    class_name: str
    history_path: str

    def __init__(
        self,
        old_key_name: str,
        old_key: FileFields,
        new_key_name: str,
        new_key: FileFields,
        file_name: str,
        class_name: str,
        history_path: str,
        *args: object,
    ) -> None:
        self.old_key_name = old_key_name
        self.old_key = old_key
        self.new_key_name = new_key_name
        self.new_key = new_key
        self.file_name = file_name
        self.class_name = class_name
        self.history_path = history_path
        super().__init__(*args)


class NewKeyAction(Exception):
    new_key_name: str
    new_key: FileFields
    file_name: str
    class_name: str
    history_path: str

    def __init__(
        self,
        new_key_name: str,
        new_key: FileFields,
        file_name: str,
        class_name: str,
        history_path: str,
        *args: object,
    ) -> None:
        self.new_key_name = new_key_name
        self.new_key = new_key
        self.file_name = file_name
        self.class_name = class_name
        self.history_path = history_path
        super().__init__(*args)


class ApplyHistoryAction(Exception):
    file_name: str
    class_name: str
    history: dict[str, FileFields]

    def __init__(
        self,
        file_name: str,
        class_name: str,
        history: dict[str, FileFields],
        *args: object,
    ) -> None:
        self.file_name = file_name
        self.class_name = class_name
        self.history = history

        super().__init__(*args)


class RemoveHistoryKeyAsIsAction(Exception):
    file_name: str
    class_name: str
    history_path: str
    old_key: str

    def __init__(
        self,
        file_name: str,
        old_key: str,
        class_name: str,
        history_path: str,
        *args: object,
    ) -> None:
        self.old_key = old_key
        self.file_name = file_name
        self.class_name = class_name
        self.history_path = history_path
        super().__init__(*args)


class RemoveHistoryCleanAction(Exception):
    file_name: str
    class_name: str
    history_path: str
    old_key: FileFields
    old_key_name: str

    def __init__(
        self,
        file_name: str,
        old_key_name: str,
        old_key: FileFields,
        class_name: str,
        history_path: str,
        *args: object,
    ) -> None:
        self.old_key_name = old_key_name
        self.old_key = old_key
        self.file_name = file_name
        self.class_name = class_name
        self.history_path = history_path
        super().__init__(*args)


class ReAddHistoryAction(Exception):
    file_name: str
    class_name: str
    old_key_name: str
    old_key: FileFields

    def __init__(
        self,
        file_name: str,
        old_key_name: str,
        old_key: FileFields,
        class_name: str,
        history_path: str,
        *args: object,
    ) -> None:
        self.old_key_name = old_key_name
        self.old_key = old_key
        self.file_name = file_name
        self.class_name = class_name
        self.history_path = history_path
        super().__init__(*args)


ActionType: TypeAlias = (
    RenameAction
    | NewKeyAction
    | ApplyHistoryAction
    | RemoveHistoryKeyAsIsAction
    | RemoveHistoryCleanAction
    | ReAddHistoryAction
)

ACTION_TYPE_ERRORS = (
    RenameAction,
    NewKeyAction,
    RemoveHistoryKeyAsIsAction,
    RemoveHistoryCleanAction,
    ReAddHistoryAction,
)


class Executor:
    @staticmethod
    def handle_action(error: ActionType) -> None:
        if isinstance(error, ApplyHistoryAction):
            try:
                for key in error.history:
                    apply_history(
                        error.history[key], key, error.file_name, error.class_name
                    )
                return
            except Exception as e:
                LOGGER.exception("Applying history failed, stopping,%s" % e)
                raise e

        with open(error.history_path) as history_in:
            history = parse(history_in)
            if error.class_name not in history:
                history[error.class_name] = {}
        if isinstance(error, RenameAction):
            try:
                rename(
                    error.old_key,
                    error.old_key_name,
                    error.new_key,
                    error.new_key_name,
                    error.file_name,
                    error.class_name,
                )
                with open(error.history_path, "w") as history_out:
                    history[error.class_name].pop(error.old_key_name)
                    history[error.class_name][error.new_key_name] = error.new_key
                    dump(history, history_out)
            except Exception as e:
                LOGGER.exception("Renaming Failed, stopping,%s" % e)
                raise e
        elif isinstance(error, NewKeyAction):
            try:
                apply_history(
                    error.new_key, error.new_key_name, error.file_name, error.class_name
                )
                with open(error.history_path, "w") as history_out:
                    history[error.class_name][error.new_key_name] = error.new_key
                    dump(history, history_out)
            except Exception as e:
                LOGGER.exception("Adding new key Failed, stopping,%s" % e)
                raise e
        elif isinstance(error, RemoveHistoryKeyAsIsAction):
            try:
                with open(error.history_path, "w") as history_out:
                    history.pop(error.old_key)
                    dump(history, history_out)
            except Exception as e:
                LOGGER.exception(
                    "Removing old key from history Failed, stopping,%s" % e
                )
                raise e
        elif isinstance(error, RemoveHistoryCleanAction):
            try:
                purge(
                    error.old_key_name, error.old_key, error.file_name, error.class_name
                )
                with open(error.history_path, "w") as history_out:
                    history.pop(error.old_key)
                    dump(history, history_out)
            except Exception as e:
                LOGGER.exception("Purging old key from history Failed, stopping,%s" % e)
                raise e
        elif isinstance(error, ReAddHistoryAction):
            try:
                apply_history(
                    error.old_key, error.old_key_name, error.file_name, error.class_name
                )
                with open(error.history_path, "w") as history_out:
                    history[error.class_name][error.old_key_name] = error.old_key
                    dump(history, history_out)
            except Exception as e:
                LOGGER.exception(
                    "Re adding old key from history Failed, stopping,%s" % e
                )
                raise e

        raise Exception("Unknown command,%s" % error)
