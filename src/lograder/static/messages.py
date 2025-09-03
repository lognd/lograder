from colorama import Fore

class DefaultMessageConfig:
    DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE: str = f"{Fore.LIGHTRED_EX}BUILD WAS UNSUCCESSFUL.{Fore.RESET}"
    DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE: str = f"{Fore.LIGHTRED_EX}BUILD WAS UNSUCCESSFUL{Fore.RESET}"

    @classmethod
    def set(cls, key: str, value: str):
        if hasattr(cls, key):
            setattr(cls, key, value)