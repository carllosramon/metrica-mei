"""A API recusa subir sem um segredo à altura.

Sem isto o servidor ligava, respondia no /health e só falhava no primeiro
login, longe de quem estava olhando a subida. E o valor de exemplo do
.env.example, que está no repositório público, passava como segredo.
"""

import pytest

from app.config import Settings
from app.main import verificar_configuracao
from app.security.jwt import TokenService

SEGREDO_BOM = "um-segredo-de-teste-com-mais-de-32-caracteres"


@pytest.mark.parametrize(
    "segredo",
    [None, "", "curto", "   ", " " * 40],
)
def test_recusa_subir_sem_segredo_a_altura(segredo):
    # O argumento explícito vence o ambiente e o .env, então o teste não
    # depende do que a máquina de quem roda tem configurado.
    with pytest.raises(ValueError, match="32 caracteres"):
        verificar_configuracao(Settings(jwt_secret=segredo))


def test_sobe_com_o_segredo_a_altura():
    verificar_configuracao(Settings(jwt_secret=SEGREDO_BOM))


def test_o_servico_de_token_faz_a_mesma_exigencia():
    # A exigência mora no serviço, então vale para quem o constrói sem
    # passar pela subida, como um uvicorn com o lifespan desligado.
    with pytest.raises(ValueError, match="32 caracteres"):
        TokenService("curto")
