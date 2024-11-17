import os
from typing import Literal


class Settings:
    def __init__(self) -> None:
        self.mode: Literal["flask"] | Literal["asyncio"] = (
            "flask" if os.environ.get("mode", "flask").lower() == "flask" else "asyncio"
        )
        self.purge: bool = os.environ.get("purge", "true").lower() == "true"
        self.purge_on_unhandled = (
            os.environ.get("purge_on_unhandled", "true").lower() == "true"
            if os.environ.get("purge_on_unhandled") is not None
            else self.purge
        )
        self.purge_on_unhandled_mime = (
            os.environ.get("purge_on_unhandled_mime", "true").lower() == "true"
            if os.environ.get("purge_on_unhandled_mime") is not None
            else self.purge_on_unhandled
        )
        self.purge_on_unhandled_file = (
            os.environ.get("purge_on_unhandled_file", "true").lower() == "true"
            if os.environ.get("purge_on_unhandled_file") is not None
            else self.purge_on_unhandled
        )
        self.purge_on_unhandled_werkzeug = (
            os.environ.get("purge_on_unhandled_werkzeug", "true").lower() == "true"
            if os.environ.get("purge_on_unhandled_werkzeug") is not None
            else self.purge_on_unhandled
        )
        self.purge_on_unhandled_starlette = (
            os.environ.get("purge_on_unhandled_starlette", "true").lower() == "true"
            if os.environ.get("purge_on_unhandled_starlette") is not None
            else self.purge_on_unhandled
        )


SETTINGS = Settings()
