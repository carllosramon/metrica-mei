from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class PasswordService:
    def __init__(self):
        self._hasher = PasswordHasher()
        # Hash de uma senha que não pertence a ninguém, usado apenas para
        # gastar o mesmo tempo de verificação quando não há usuário para
        # verificar. Precisa ser um hash Argon2 de verdade: contra um
        # texto qualquer o verify falha de imediato e não custa nada.
        self._hash_sem_dono = self._hasher.hash(
            "nenhuma-conta-tem-esta-senha"
        )

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def consumir_tempo_de_verificacao(self, password: str) -> None:
        """Verifica contra um hash descartável, só para custar o tempo.

        Quando o e-mail não existe, o Argon2 nunca rodava e a resposta
        saía em cerca de 1 ms, contra dezenas de milissegundos de um
        e-mail real. As duas respostas são iguais no texto e no status,
        mas o tempo permitia enumerar quem tem conta no sistema.
        """
        self.verify(password, self._hash_sem_dono)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False