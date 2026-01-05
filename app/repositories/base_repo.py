from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    async def create(self, data):
        pass
    
    @abstractmethod 
    async def get_by_id(self, id: int):
        pass
    