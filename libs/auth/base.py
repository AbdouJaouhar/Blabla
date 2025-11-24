from abc import ABC, abstractmethod


class AuthBackend(ABC):
    @abstractmethod
    async def authenticate(self, **kwargs):
        pass
