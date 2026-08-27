from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


class TokenService:
    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expires_minutes: int = 30,
    ):
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