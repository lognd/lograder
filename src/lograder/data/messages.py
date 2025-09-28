from colorama import Fore


class MessageConfig:
    DEFAULT_RAW_TITLE: str = f"<{Fore.MAGENTA}RAW STRING OUTPUT{Fore.RESET}>"
    DEFAULT_BUILD_ERROR: str = f"<{Fore.RED}BUILD ERROR{Fore.RED}>"
