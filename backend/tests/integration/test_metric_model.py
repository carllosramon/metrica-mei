from sqlalchemy import UniqueConstraint

from app.database import models
from app.database.connection import Base


def test_metric_model_maps_expected_table():
    metric_model = getattr(
        models,
        "MetricModel",
        None,
    )

    assert metric_model is not None

    table = Base.metadata.tables["metricas"]

    assert set(table.columns.keys()) == {
        "id",
        "conteudo_id",
        "visualizacoes",
        "curtidas",
        "comentarios",
        "compartilhamentos",
        "alcance",
        "data_referencia",
        "criado_em",
    }

def test_metric_content_foreign_key_uses_on_delete_cascade():
    table = Base.metadata.tables["metricas"]

    foreign_keys = list(
        table.c.conteudo_id.foreign_keys
    )

    assert len(foreign_keys) == 1
    assert (
        foreign_keys[0].target_fullname
        == "conteudos.id"
    )
    assert foreign_keys[0].ondelete == "CASCADE"

def test_metric_model_has_unique_content_reference_date():
    table = Base.metadata.tables["metricas"]

    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(
            constraint,
            UniqueConstraint,
        )
    ]

    matching = [
        constraint
        for constraint in unique_constraints
        if {
            column.name
            for column in constraint.columns
        }
        == {
            "conteudo_id",
            "data_referencia",
        }
    ]

    assert len(matching) == 1
    assert (
        matching[0].name
        == "uq_metricas_conteudo_data_referencia"
    )
