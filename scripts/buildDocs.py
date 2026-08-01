import json
import subprocess
import sys
from pathlib import Path
from pydantic import TypeAdapter

# import type alias and response model
from enrichapi.models.request import EnrichmentRequest
from enrichapi.models.response import RootApiResponse


def buildJsonSchemas(projectRoot: Path):
    """Generates Pydantic JSON schemas into docs/schemas/."""
    print("Generating JSON Schemas...")
    
    schemasDir = projectRoot / "docs" / "schemas"
    schemasDir.mkdir(parents=True, exist_ok=True)

    # export request schema (using TypeAdapter for Annotated polymorphic union)
    requestAdapter = TypeAdapter(EnrichmentRequest)
    requestSchema = requestAdapter.json_schema()
    
    reqPath = schemasDir / "enrichmentRequestSchema.json"
    with open(reqPath, "w", encoding="utf-8") as f:
        json.dump(requestSchema, f, indent=2, ensure_ascii=False)
    print(f"    Created: {reqPath.relative_to(projectRoot)}")

    # export response schema (BaseModel)
    responseSchema = RootApiResponse.model_json_schema()
    
    resPath = schemasDir / "rootApiResponseSchema.json"
    with open(resPath, "w", encoding="utf-8") as f:
        json.dump(responseSchema, f, indent=2, ensure_ascii=False)
    print(f"    Created: {resPath.relative_to(projectRoot)}")


def buildPdocApi(projectRoot: Path):
    """Executes pdoc to generate HTML documentation into docs/api/."""
    print("\nGenerating pdoc API HTML documentation...")
    
    apiDir = projectRoot / "docs" / "api"
    apiDir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pdoc",
        "-o",
        str(apiDir),
        "enrichapi",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"    API docs generated in: {apiDir.relative_to(projectRoot)}/")
    except subprocess.CalledProcessError as e:
        print(f"    pdoc build failed:\n{e.stderr}")
        sys.exit(1)


def main():
    projectRoot = Path(__file__).resolve().parent.parent
    print(f"Starting documentation build for project root: {projectRoot}\n")
    
    buildJsonSchemas(projectRoot)
    buildPdocApi(projectRoot)
    
    print("\nAll documentation generated successfully!")


if __name__ == "__main__":
    main()