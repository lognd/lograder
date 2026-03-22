from __future__ import annotations

from pathlib import Path
from typing import Literal

from ...types.executable.cli_args import CLIArgs, CLIField


class CurlArgs(CLIArgs):
    # URL(s)
    urls: list[str] = CLIField(default_factory=list, positional=True)

    # Request method / body
    request: str | None = CLIField(default=None, flag="-X")
    data: list[str] = CLIField(default_factory=list, flag="--data", repeat=True)
    data_binary: list[str | Path] = CLIField(
        default_factory=list, flag="--data-binary", repeat=True
    )
    data_urlencode: list[str] = CLIField(
        default_factory=list, flag="--data-urlencode", repeat=True
    )
    form: list[str] = CLIField(default_factory=list, flag="-F", repeat=True)
    get: bool = CLIField(default=False, flag="-G")

    # Headers / auth
    headers: list[str] = CLIField(default_factory=list, flag="-H", repeat=True)
    user_agent: str | None = CLIField(default=None, flag="-A")
    user: str | None = CLIField(default=None, flag="-u")
    bearer_token: str | None = CLIField(default=None, exclude=True)
    basic: bool = CLIField(default=False, flag="--basic")
    digest: bool = CLIField(default=False, flag="--digest")
    anyauth: bool = CLIField(default=False, flag="--anyauth")

    # Output / transfer behavior
    output: Path | str | None = CLIField(default=None, flag="-o")
    remote_name: bool = CLIField(default=False, flag="-O")
    remote_name_all: bool = CLIField(default=False, flag="-J")
    fail: bool = CLIField(default=False, flag="-f")
    fail_with_body: bool = CLIField(default=False, flag="--fail-with-body")
    silent: bool = CLIField(default=False, flag="-s")
    show_error: bool = CLIField(default=False, flag="-S")
    location: bool = CLIField(default=False, flag="-L")
    max_redirs: int | None = CLIField(default=None, flag="--max-redirs")
    head: bool = CLIField(default=False, flag="-I")
    include: bool = CLIField(default=False, flag="-i")
    verbose: bool = CLIField(default=False, flag="-v")

    # Retry / timeout
    retry: int | None = CLIField(default=None, flag="--retry")
    retry_delay: int | None = CLIField(default=None, flag="--retry-delay")
    retry_max_time: int | None = CLIField(default=None, flag="--retry-max-time")
    connect_timeout: int | float | None = CLIField(
        default=None, flag="--connect-timeout"
    )
    max_time: int | float | None = CLIField(default=None, flag="--max-time")

    # TLS / certificate behavior
    insecure: bool = CLIField(default=False, flag="-k")
    cacert: Path | str | None = CLIField(default=None, flag="--cacert")
    cert: Path | str | None = CLIField(default=None, flag="--cert")
    key: Path | str | None = CLIField(default=None, flag="--key")

    # Proxy
    proxy: str | None = CLIField(default=None, flag="-x")
    noproxy: str | None = CLIField(default=None, flag="--noproxy")

    # File transfer
    upload_file: Path | str | None = CLIField(default=None, flag="-T")
    ftp_create_dirs: bool = CLIField(default=False, flag="--ftp-create-dirs")

    # Misc
    compressed: bool = CLIField(default=False, flag="--compressed")
    ipv4: bool = CLIField(default=False, flag="-4")
    ipv6: bool = CLIField(default=False, flag="-6")
    http1_1: bool = CLIField(default=False, flag="--http1.1")
    http2: bool = CLIField(default=False, flag="--http2")
    output_headers: Path | str | None = CLIField(default=None, flag="-D")

    # Escape hatch
    extra: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args: list[str] = []

        if self.request is not None:
            args.extend(["-X", self.request])

        for item in self.data:
            args.extend(["--data", str(item)])
        for item in self.data_binary:
            args.extend(["--data-binary", str(item)])
        for item in self.data_urlencode:
            args.extend(["--data-urlencode", str(item)])
        for item in self.form:
            args.extend(["-F", str(item)])
        if self.get:
            args.append("-G")

        for header in self.headers:
            args.extend(["-H", header])
        if self.user_agent is not None:
            args.extend(["-A", self.user_agent])
        if self.user is not None:
            args.extend(["-u", self.user])
        if self.bearer_token is not None:
            args.extend(["-H", f"Authorization: Bearer {self.bearer_token}"])
        if self.basic:
            args.append("--basic")
        if self.digest:
            args.append("--digest")
        if self.anyauth:
            args.append("--anyauth")

        if self.output is not None:
            args.extend(["-o", str(self.output)])
        if self.remote_name:
            args.append("-O")
        if self.remote_name_all:
            args.append("-J")
        if self.fail:
            args.append("-f")
        if self.fail_with_body:
            args.append("--fail-with-body")
        if self.silent:
            args.append("-s")
        if self.show_error:
            args.append("-S")
        if self.location:
            args.append("-L")
        if self.max_redirs is not None:
            args.extend(["--max-redirs", str(self.max_redirs)])
        if self.head:
            args.append("-I")
        if self.include:
            args.append("-i")
        if self.verbose:
            args.append("-v")

        if self.retry is not None:
            args.extend(["--retry", str(self.retry)])
        if self.retry_delay is not None:
            args.extend(["--retry-delay", str(self.retry_delay)])
        if self.retry_max_time is not None:
            args.extend(["--retry-max-time", str(self.retry_max_time)])
        if self.connect_timeout is not None:
            args.extend(["--connect-timeout", str(self.connect_timeout)])
        if self.max_time is not None:
            args.extend(["--max-time", str(self.max_time)])

        if self.insecure:
            args.append("-k")
        if self.cacert is not None:
            args.extend(["--cacert", str(self.cacert)])
        if self.cert is not None:
            args.extend(["--cert", str(self.cert)])
        if self.key is not None:
            args.extend(["--key", str(self.key)])

        if self.proxy is not None:
            args.extend(["-x", self.proxy])
        if self.noproxy is not None:
            args.extend(["--noproxy", self.noproxy])

        if self.upload_file is not None:
            args.extend(["-T", str(self.upload_file)])
        if self.ftp_create_dirs:
            args.append("--ftp-create-dirs")

        if self.compressed:
            args.append("--compressed")
        if self.ipv4:
            args.append("-4")
        if self.ipv6:
            args.append("-6")
        if self.http1_1:
            args.append("--http1.1")
        if self.http2:
            args.append("--http2")
        if self.output_headers is not None:
            args.extend(["-D", str(self.output_headers)])

        args.extend(str(url) for url in self.urls)
        args.extend(str(x) for x in self.extra)
        return args


class WingetArgs(CLIArgs):
    """
    Generic winget invocation:
        winget <subcommand> [query/package] [options...]

    Examples:
        winget install Python.Python.3.12 --silent --accept-package-agreements
        winget search git
        winget upgrade --all
    """

    subcommand: Literal[
        "install",
        "upgrade",
        "uninstall",
        "search",
        "show",
        "list",
        "source",
        "configure",
        "download",
        "export",
        "import",
        "hash",
        "validate",
        "settings",
        "features",
        "pin",
    ] = CLIField(positional=True)

    query: str | None = CLIField(default=None, positional=True)

    # Selection / identity
    id: str | None = CLIField(default=None, flag="--id")
    name: str | None = CLIField(default=None, flag="--name")
    moniker: str | None = CLIField(default=None, flag="--moniker")
    version: str | None = CLIField(default=None, flag="--version")
    source: str | None = CLIField(default=None, flag="--source")
    exact: bool = CLIField(default=False, flag="--exact")

    # Install / upgrade behavior
    scope: Literal["user", "machine"] | None = CLIField(default=None, flag="--scope")
    silent: bool = CLIField(default=False, flag="--silent")
    interactive: bool = CLIField(default=False, flag="--interactive")
    force: bool = CLIField(default=False, flag="--force")
    purge: bool = CLIField(default=False, flag="--purge")
    reinstall: bool = CLIField(default=False, flag="--reinstall")
    all: bool = CLIField(default=False, flag="--all")
    include_unknown: bool = CLIField(default=False, flag="--include-unknown")
    uninstall_previous: bool = CLIField(default=False, flag="--uninstall-previous")

    # Agreement / safety switches
    accept_package_agreements: bool = CLIField(
        default=False, flag="--accept-package-agreements"
    )
    accept_source_agreements: bool = CLIField(
        default=False, flag="--accept-source-agreements"
    )
    disable_interactivity: bool = CLIField(
        default=False, flag="--disable-interactivity"
    )

    # Logging / output
    location: Path | str | None = CLIField(default=None, flag="--location")
    log: Path | str | None = CLIField(default=None, flag="--log")
    verbose: bool = CLIField(default=False, flag="--verbose")
    ignore_warnings: bool = CLIField(default=False, flag="--ignore-warnings")

    # Installer pass-through
    override: str | None = CLIField(default=None, flag="--override")
    custom: list[str] = CLIField(default_factory=list, flag="--custom", repeat=True)

    # Export / import / manifest-y flows
    manifest: Path | str | None = CLIField(default=None, flag="--manifest")
    output: Path | str | None = CLIField(default=None, flag="--output")
    hash_file: Path | str | None = CLIField(default=None, positional=True)

    # Escape hatch
    extra: list[str] = CLIField(default_factory=list, positional=True)


class AptGetArgs(CLIArgs):
    """
    Generic apt-get invocation:
        apt-get <subcommand> [packages...] [options...]

    Examples:
        apt-get update
        apt-get install -y curl git
        apt-get remove -y nginx
    """

    subcommand: Literal[
        "update",
        "upgrade",
        "dist-upgrade",
        "install",
        "remove",
        "purge",
        "autoremove",
        "clean",
        "autoclean",
        "check",
        "download",
        "source",
        "build-dep",
        "satisfy",
    ] = CLIField(positional=True)

    packages: list[str] = CLIField(default_factory=list, positional=True)

    # Confirmation / interaction
    assume_yes: bool = CLIField(default=False, flag="-y")
    assume_no: bool = CLIField(default=False, flag="--assume-no")
    quiet: bool = CLIField(default=False, flag="-q")
    quiet_level_2: bool = CLIField(default=False, flag="-qq")
    simulate: bool = CLIField(default=False, flag="-s")

    # Behavior
    download_only: bool = CLIField(default=False, flag="-d")
    fix_broken: bool = CLIField(default=False, flag="-f")
    fix_missing: bool = CLIField(default=False, flag="-m")
    no_download: bool = CLIField(default=False, flag="--no-download")
    reinstall: bool = CLIField(default=False, flag="--reinstall")
    only_upgrade: bool = CLIField(default=False, flag="--only-upgrade")
    install_recommends: bool | None = CLIField(default=None, exclude=True)
    install_suggests: bool | None = CLIField(default=None, exclude=True)
    purge_mode: bool = CLIField(default=False, flag="--purge")

    # Targeting / release / arch
    target_release: str | None = CLIField(default=None, flag="-t")
    option: list[str] = CLIField(default_factory=list, flag="-o", repeat=True)
    host_architecture: str | None = CLIField(default=None, flag="-a")
    arch_only: str | None = CLIField(default=None, flag="--arch-only")

    # Misc
    print_uris: bool = CLIField(default=False, flag="--print-uris")
    no_install_recommends: bool = CLIField(
        default=False, flag="--no-install-recommends"
    )
    no_install_suggests: bool = CLIField(default=False, flag="--no-install-suggests")
    verbose_versions: bool = CLIField(default=False, flag="-V")

    # Escape hatch
    extra: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args: list[str] = [self.subcommand]

        if self.assume_yes:
            args.append("-y")
        if self.assume_no:
            args.append("--assume-no")
        if self.quiet:
            args.append("-q")
        if self.quiet_level_2:
            args.append("-qq")
        if self.simulate:
            args.append("-s")

        if self.download_only:
            args.append("-d")
        if self.fix_broken:
            args.append("-f")
        if self.fix_missing:
            args.append("-m")
        if self.no_download:
            args.append("--no-download")
        if self.reinstall:
            args.append("--reinstall")
        if self.only_upgrade:
            args.append("--only-upgrade")
        if self.purge_mode:
            args.append("--purge")

        if self.install_recommends is True:
            args.append("--install-recommends")
        elif self.install_recommends is False:
            args.append("--no-install-recommends")

        if self.install_suggests is True:
            args.append("--install-suggests")
        elif self.install_suggests is False:
            args.append("--no-install-suggests")

        if self.target_release is not None:
            args.extend(["-t", self.target_release])

        for opt in self.option:
            args.extend(["-o", opt])

        if self.host_architecture is not None:
            args.extend(["-a", self.host_architecture])
        if self.arch_only is not None:
            args.extend(["--arch-only", self.arch_only])

        if self.print_uris:
            args.append("--print-uris")
        if self.no_install_recommends:
            args.append("--no-install-recommends")
        if self.no_install_suggests:
            args.append("--no-install-suggests")
        if self.verbose_versions:
            args.append("-V")

        args.extend(self.packages)
        args.extend(str(x) for x in self.extra)
        return args


class RPMArgs(CLIArgs):
    """
    Generic rpm invocation.

    Common modes:
        rpm -i package.rpm
        rpm -U package.rpm
        rpm -e pkgname
        rpm -q pkgname
        rpm -qa
        rpm -ql pkgname
        rpm -qp file.rpm

    The primary mode flags are mutually exclusive in real usage, so
    this model expects you to set one main mode at a time.
    """

    # Main mode
    install: bool = CLIField(default=False, flag="-i")
    upgrade: bool = CLIField(default=False, flag="-U")
    freshen: bool = CLIField(default=False, flag="-F")
    erase: bool = CLIField(default=False, flag="-e")
    query: bool = CLIField(default=False, flag="-q")
    verify: bool = CLIField(default=False, flag="-V")
    import_key: bool = CLIField(default=False, flag="--import")
    initdb: bool = CLIField(default=False, flag="--initdb")
    rebuilddb: bool = CLIField(default=False, flag="--rebuilddb")

    # Targets
    packages: list[str | Path] = CLIField(default_factory=list, positional=True)

    # Install/upgrade behavior
    hash: bool = CLIField(default=False, flag="-h")
    verbose: bool = CLIField(default=False, flag="-v")
    force: bool = CLIField(default=False, flag="--force")
    nodeps: bool = CLIField(default=False, flag="--nodeps")
    replacepkgs: bool = CLIField(default=False, flag="--replacepkgs")
    replacefiles: bool = CLIField(default=False, flag="--replacefiles")
    oldpackage: bool = CLIField(default=False, flag="--oldpackage")
    test: bool = CLIField(default=False, flag="--test")
    nosignature: bool = CLIField(default=False, flag="--nosignature")
    nodigest: bool = CLIField(default=False, flag="--nodigest")
    prefix: Path | str | None = CLIField(default=None, flag="--prefix")
    relocations: list[str] = CLIField(
        default_factory=list, flag="--relocate", repeat=True
    )

    # Query selectors
    all: bool = CLIField(default=False, flag="-a")
    package_file: bool = CLIField(default=False, flag="-p")
    info: bool = CLIField(default=False, flag="-i")
    list_files: bool = CLIField(default=False, flag="-l")
    changelog: bool = CLIField(default=False, flag="-c")
    scripts: bool = CLIField(default=False, flag="--scripts")
    requires: bool = CLIField(default=False, flag="-R")
    provides: bool = CLIField(default=False, flag="--provides")
    whatprovides: str | None = CLIField(default=None, flag="--whatprovides")
    whatrequires: str | None = CLIField(default=None, flag="--whatrequires")
    queryformat: str | None = CLIField(default=None, flag="--queryformat")

    # DB / root
    root: Path | str | None = CLIField(default=None, flag="--root")
    dbpath: Path | str | None = CLIField(default=None, flag="--dbpath")

    # Escape hatch
    extra: list[str] = CLIField(default_factory=list, positional=True)

    def to_arguments(self) -> list[str]:
        args: list[str] = []

        if self.install:
            args.append("-i")
        if self.upgrade:
            args.append("-U")
        if self.freshen:
            args.append("-F")
        if self.erase:
            args.append("-e")
        if self.query:
            args.append("-q")
        if self.verify:
            args.append("-V")
        if self.import_key:
            args.append("--import")
        if self.initdb:
            args.append("--initdb")
        if self.rebuilddb:
            args.append("--rebuilddb")

        if self.hash:
            args.append("-h")
        if self.verbose:
            args.append("-v")
        if self.force:
            args.append("--force")
        if self.nodeps:
            args.append("--nodeps")
        if self.replacepkgs:
            args.append("--replacepkgs")
        if self.replacefiles:
            args.append("--replacefiles")
        if self.oldpackage:
            args.append("--oldpackage")
        if self.test:
            args.append("--test")
        if self.nosignature:
            args.append("--nosignature")
        if self.nodigest:
            args.append("--nodigest")
        if self.prefix is not None:
            args.extend(["--prefix", str(self.prefix)])
        for relocation in self.relocations:
            args.extend(["--relocate", relocation])

        if self.all:
            args.append("-a")
        if self.package_file:
            args.append("-p")
        if self.info:
            args.append("-i")
        if self.list_files:
            args.append("-l")
        if self.changelog:
            args.append("-c")
        if self.scripts:
            args.append("--scripts")
        if self.requires:
            args.append("-R")
        if self.provides:
            args.append("--provides")
        if self.whatprovides is not None:
            args.extend(["--whatprovides", self.whatprovides])
        if self.whatrequires is not None:
            args.extend(["--whatrequires", self.whatrequires])
        if self.queryformat is not None:
            args.extend(["--queryformat", self.queryformat])

        if self.root is not None:
            args.extend(["--root", str(self.root)])
        if self.dbpath is not None:
            args.extend(["--dbpath", str(self.dbpath)])

        args.extend(str(x) for x in self.packages)
        args.extend(str(x) for x in self.extra)
        return args
