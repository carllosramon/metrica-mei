import ast
from pathlib import Path


VERSIONS_DIR = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
)


def revision_id_from_file(path: Path) -> str:
    tree = ast.parse(
        path.read_text(encoding="utf-8")
    )

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "revision"
            ):
                assert isinstance(
                    node.value,
                    ast.Constant,
                )
                assert isinstance(
                    node.value.value,
                    str,
                )

                return node.value.value

    raise AssertionError(
        f"Migration sem revision: {path.name}"
    )


def test_revision_ids_fit_alembic_default_version_column():
    migration_files = sorted(
        VERSIONS_DIR.glob("*.py")
    )

    assert migration_files

    for path in migration_files:
        revision = revision_id_from_file(path)

        assert len(revision) <= 32, (
            f"{path.name}: revision '{revision}' "
            "ultrapassa 32 caracteres."
        )
