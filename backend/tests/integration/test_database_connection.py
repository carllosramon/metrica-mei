from datetime import date, datetime, timezone

from sqlalchemy import event, select, text

from app.database.connection import (
    Base,
    _enable_sqlite_foreign_keys,
    create_engine_from_url,
    create_session_factory,
)
from app.database.models import (
    ContentModel,
    MetricModel,
    UserModel,
)


def test_sqlite_engine_enables_foreign_keys():
    engine = create_engine_from_url(
        "sqlite:///:memory:"
    )

    try:
        with engine.connect() as connection:
            foreign_keys_enabled = connection.execute(
                text("PRAGMA foreign_keys")
            ).scalar_one()

        assert foreign_keys_enabled == 1
    finally:
        engine.dispose()

def test_sqlite_deleting_content_cascades_metrics():
    engine = create_engine_from_url(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(engine)

    session_factory = create_session_factory(
        engine
    )

    try:
        with session_factory() as session:
            user = UserModel(
                nome="Teste",
                email="teste@example.com",
                senha_hash="hash",
                criado_em=datetime.now(timezone.utc),
            )

            session.add(user)
            session.flush()

            content = ContentModel(
                usuario_id=user.id,
                titulo="Conteúdo",
                plataforma="Instagram",
                tipo="Reel",
                data_publicacao=date.today(),
                criado_em=datetime.now(timezone.utc),
            )

            session.add(content)
            session.flush()

            metric = MetricModel(
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=20,
                comentarios=5,
                compartilhamentos=3,
                alcance=80,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )

            session.add(metric)
            session.commit()

            metric_id = metric.id

            session.delete(content)
            session.commit()

            deleted_metric = session.scalar(
                select(MetricModel).where(
                    MetricModel.id == metric_id
                )
            )

            assert deleted_metric is None
    finally:
        engine.dispose()


def test_postgres_engine_does_not_use_sqlite_settings():
    # create_engine resolve o dialeto e importa o driver, mas não conecta.
    # Isso permite verificar o caminho não-SQLite sem um servidor no ar.
    engine = create_engine_from_url(
        "postgresql+psycopg://usuario:senha@localhost:5432/metricamei"
    )

    try:
        assert engine.dialect.name == "postgresql"

        # check_same_thread e o PRAGMA são remendos do SQLite: no Postgres
        # o primeiro nem existe como parâmetro, e o segundo quebraria a
        # conexão logo na abertura.
        assert "check_same_thread" not in engine.dialect.create_connect_args(
            engine.url
        )[1]

        assert not event.contains(
            engine,
            "connect",
            _enable_sqlite_foreign_keys,
        )
    finally:
        engine.dispose()


def test_sqlite_engine_keeps_its_own_settings():
    engine = create_engine_from_url(
        "sqlite:///:memory:"
    )

    try:
        assert engine.dialect.name == "sqlite"

        assert event.contains(
            engine,
            "connect",
            _enable_sqlite_foreign_keys,
        )
    finally:
        engine.dispose()
