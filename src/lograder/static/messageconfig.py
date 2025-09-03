from colorama import Fore


class LograderMessageConfig:
    DEFAULT_BUILD_ERROR_OVERRIDE_MESSAGE: str = (
        f"BUILD WAS UNSUCCESSFUL."
    )
    DEFAULT_BUILD_ERROR_EXECUTABLE_NAME: str = (
        f"{Fore.RED}<NO EXECUTABLE GENERATED>{Fore.RESET}"
    )
    DEFAULT_UNIT_TEST_EXPECTED_OUTPUT_MESSAGE: str = (
        f"{Fore.YELLOW}<UNIT TEST CASE HAS NO `EXPECTED OUTPUT` TO COMPARE>{Fore.RESET}"
    )

    @classmethod
    def set(cls, key: str, value: str):
        if hasattr(cls, key):
            setattr(cls, key, value)
