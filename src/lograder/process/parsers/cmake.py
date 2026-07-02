from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from lograder.pipeline.types.artifacts import CMakeArtifact, CMakeFileArtifact


class _CommonArtifactFields(BaseModel):
    name: str
    target_type: str
    target_id: str | None
    target_json: Path
    config_name: str | None
    project_name: str | None
    source_dir: Path | None
    build_dir: Path
    raw_target: dict[str, Any]

    def to_artifact(self) -> CMakeArtifact:
        return CMakeArtifact(
            name=self.name,
            target_type=self.target_type,
            target_id=self.target_id,
            target_json=self.target_json,
            config_name=self.config_name,
            project_name=self.project_name,
            source_dir=self.source_dir,
            build_dir=self.build_dir,
            raw_target=self.raw_target,
        )

    def to_file_artifact(
        self, artifact_path: Path, cmake_path: str
    ) -> CMakeFileArtifact:
        return CMakeFileArtifact(
            name=self.name,
            target_type=self.target_type,
            target_id=self.target_id,
            target_json=self.target_json,
            config_name=self.config_name,
            project_name=self.project_name,
            source_dir=self.source_dir,
            build_dir=self.build_dir,
            raw_target=self.raw_target,
            path=artifact_path,
            artifact_path_from_cmake=cmake_path,
        )


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

            target_source_dir = (
                Path(target["sourceDirectory"]).resolve()
                if target.get("sourceDirectory")
                else None
            )
            target_build_dir = Path(target.get("buildDirectory", build_dir)).resolve()
            common_fields = _CommonArtifactFields(
                name=name,
                target_type=target_type,
                target_id=target_id,
                target_json=target_json_path,
                config_name=config_name,
                project_name=target_ref.get("projectName"),
                source_dir=target_source_dir,
                build_dir=target_build_dir,
                raw_target=target,
            )

            artifacts = target.get("artifacts", [])

            if not artifacts:
                results.append(common_fields.to_artifact())
                continue

            for artifact in artifacts:
                cmake_path = artifact["path"]
                artifact_path = Path(cmake_path)

                if not artifact_path.is_absolute():
                    artifact_path = build_dir / artifact_path

                artifact_path = artifact_path.resolve()

                if require_exists or artifact_path.is_file():
                    results.append(
                        common_fields.to_file_artifact(artifact_path, cmake_path)
                    )
                else:
                    results.append(common_fields.to_artifact())

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

    # cmake index format: reply[client][query_name] = {kind, version, jsonFile}
    for response in client_reply.values():
        if (
            response.get("kind") == "codemodel"
            and response.get("version", {}).get("major") == 2
        ):
            return cast(dict[str, Any], response)

    raise KeyError(f"No codemodel-v2 response found for {client_name!r}")
