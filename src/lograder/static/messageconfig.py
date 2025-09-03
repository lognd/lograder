from colorama import Fore


class LograderMessageConfig:
    DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE: str = (
        f"BUILD WAS UNSUCCESSFUL."
    )
    DEFAULT_BUILD_ERROR_EXECUTABLE_NAME: str = (
        f"{Fore.RED}<NO EXECUTABLE GENERATED>{Fore.RESET}"
    )

    @classmethod
    def set(cls, key: str, value: str):
        if hasattr(cls, key):
            setattr(cls, key, value)
