from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


MODEL_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "model_manifest.json"
)


class ModelSpec(BaseModel):
    model: str = Field(
        min_length=1
    )

    revision: str = Field(
        pattern=r"^[0-9a-f]{40}$"
    )

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )


class ModelManifest(BaseModel):
    embedding: ModelSpec
    reranker: ModelSpec

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )


model_manifest = ModelManifest.model_validate_json(
    MODEL_MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)