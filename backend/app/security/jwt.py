from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


TAMANHO_MINIMO_DO_SEGREDO = 32


class TokenService:
    def __init__(
        self,
        secret: str | None,
        algorithm: str = "HS256",
        expires_minutes: int = 30,
    ):
        # O segredo assina todo token. Vazio ou curto, qualquer um forjaria
        # um token para qualquer conta. A exigência mora aqui, e não só na
        # subida da aplicação, para valer em todo caminho que constrói o
        # serviço, inclusive os que não passam pelo lifespan.
        if (
            secret is None
            or len(secret.strip()) < TAMANHO_MINIMO_DO_SEGREDO
        ):
            raise ValueError(
                "JWT_SECRET precisa ter ao menos "
                f"{TAMANHO_MINIMO_DO_SEGREDO} caracteres."
            )

        self._secret = secret
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def create_access_token(self, user_id: int) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self._expires_minutes
        )

        return jwt.encode(
            {
                # O padrão JWT exige que a reivindicação sub seja textual,
                # então o identificador vai como string e volta convertido
                # em decode_subject.
                "sub": str(user_id),
                "exp": expires_at,
            },
            self._secret,
            algorithm=self._algorithm,
        )

    def decode_subject(self, token: str) -> int | None:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )

            return int(payload["sub"])

        # Token ausente de sub, com sub não numérico ou corrompido é
        # token sem dono: quem chama trata os três casos igual, e por isso
        # todos viram None em vez de exceções diferentes.
        except (
            ExpiredSignatureError,
            InvalidTokenError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return None