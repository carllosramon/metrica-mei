from app.database import models
from app.database.connection import Base


def test_content_model_maps_expected_table():
    content_model = getattr(
        models,
        "ContentModel",
        None,
    )

    assert content_model is not None

    table = Base.metadata.tables["conteudos"]

    assert set(table.columns.keys()) == {
        "id",
        "usuario_id",
        "titulo",
        "plataforma",
        "tipo",
        "data_publicacao",
        "criado_em",
        "url_publicacao",
    }

    assert table.c.titulo.type.length == 200
    assert table.c.plataforma.type.length == 50
    assert table.c.tipo.type.length == 50

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in table.c.usuario_id.foreign_keys
    }

    assert foreign_keys == {"usuarios.id"}
    assert table.c.usuario_id.index is True
