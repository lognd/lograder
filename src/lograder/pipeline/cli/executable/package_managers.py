from ...types.executable.external_executable import (
    BuiltInExecutable,
    FixedLocationExecutable,
    exclude,
    linux_exclusive,
    macos_exclusive,
    windows_exclusive,
)


class Curl(BuiltInExecutable):
    name: str = "curl"


@windows_exclusive
class Winget(BuiltInExecutable):
    name: str = "winget"


@linux_exclusive
class AptGet(BuiltInExecutable):
    name: str = "apt-get"


@linux_exclusive
class RPM(BuiltInExecutable):
    name: str = "rpm"
