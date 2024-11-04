import os


class Settings:
    def __init__(self) -> None:
        self.mode = (
            "flask" if os.environ.get("mode", "flask").lower() == "flask" else "asyncio"
        )


SETTINGS = Settings()
