from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from lograder.pipeline.types.artifacts import CMakeArtifact, CMakeFileArtifact


def cmake_artifacts_from_file_api(
    build_dir: Path,
    *,
    client_name: str = "client-lograder",
    require_exists: bool = True,
) -> list[CMakeArtifact]:
    """
    Parse CMake File API codemodel-v2 replies and return CMake artifacts.

    Assumes the query was created before configure at:

        <build_dir>/.cmake/api/v1/query/<client_name>/codemodel-v2

    and that CMake configure has already run.
    """

    build_dir = build_dir.resolve()
    reply_dir = build_dir / ".cmake" / "api" / "v1" / "reply"

    if not reply_dir.is_dir():
        raise FileNotFoundError(
            f"CMake File API reply directory not found: {reply_dir}"
        )

    index_files = sorted(
        reply_dir.glob("index-*.json"), key=lambda p: p.stat().st_mtime
    )
    if not index_files:
        raise FileNotFoundError(f"No CMake File API index files found in {reply_dir}")

    index_path = index_files[-1]
    index = _read_json(index_path)

    codemodel_ref = _find_codemodel_ref(index, client_name)
    codemodel_path = reply_dir / codemodel_ref["jsonFile"]
    codemodel = _read_json(codemodel_path)

    results: list[CMakeArtifact] = []

    for config in codemodel.get("configurations", []):
        config_name = config.get("name")

        for target_ref in config.get("targets", []):
            target_json_path = reply_dir / target_ref["jsonFile"]
            target = _read_json(target_json_path)

            name = target.get("name", target_ref.get("name", "<unknown>"))
            target_type = target.get("type", "<unknown>")
            target_id = target.get("id", target_ref.get("id"))

            base = {
                "name": name,
                "target_type": target_type,
                "target_id": target_id,
                "target_json": target_json_path,
                "config_name": config_name,
                "project_name": target_ref.get("projectName"),
                "source_dir": (
                    Path(target["sourceDirectory"]).resolve()
                    if target.get("sourceDirectory")
                    else None
                ),
                "build_dir": Path(target.get("buildDirectory", build_dir)).resolve(),
                "raw_target": target,
            }

            artifacts = target.get("artifacts", [])

            if not artifacts:
                results.append(CMakeArtifact(**base))
                continue

            for artifact in artifacts:
                cmake_path = artifact["path"]
                artifact_path = Path(cmake_path)

                if not artifact_path.is_absolute():
                    artifact_path = build_dir / artifact_path

                artifact_path = artifact_path.resolve()

                data = {
                    **base,
                    "path": artifact_path,
                    "artifact_path_from_cmake": cmake_path,
                }

                if require_exists:
                    results.append(CMakeFileArtifact(**data))
                else:
                    if artifact_path.is_file():
                        results.append(CMakeFileArtifact(**data))
                    else:
                        results.append(CMakeArtifact(**base))

    return results


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _find_codemodel_ref(index: dict[str, Any], client_name: str) -> dict[str, Any]:
    client_reply = index.get("reply", {}).get(client_name)

    if client_reply is None:
        available = ", ".join(index.get("reply", {}).keys())
        raise KeyError(
            f"No File API reply for {client_name!r}. "
            f"Available clients: {available or '<none>'}"
        )

    for query_reply in client_reply.values():
        for response in query_reply.get("responses", []):
            if (
                response.get("kind") == "codemodel"
                and response.get("version", {}).get("major") == 2
            ):
                return cast(dict[str, Any], response)

    raise KeyError(f"No codemodel-v2 response found for {client_name!r}")
