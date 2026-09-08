"""A API recusa subir sem o segredo do token.

Sem isto o servidor ligava, respondia no /health e só falhava no primeiro
login, longe de quem estava olhando a subida.
"""

import pytest

from app.config import Settings
from app.main import verificar_configuracao


def test_recusa_subir_sem_segredo():
    # O argumento explícito vence o ambiente e o .env, então o teste não
    # depende do que a máquina de quem roda tem configurado.
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        verificar_configuracao(Settings(jwt_secret=None))


def test_sobe_com_o_segredo_presente():
    verificar_configuracao(Settings(jwt_secret="segredo-de-teste"))
