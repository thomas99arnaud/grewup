from abc import ABC, abstractmethod

from fastapi import APIRouter, FastAPI


class BaseModule(ABC):
    name: str

    @abstractmethod
    def get_router(self) -> APIRouter:
        ...

    def on_startup(self, app: FastAPI) -> None:
        pass

    def on_shutdown(self, app: FastAPI) -> None:
        pass


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, BaseModule] = {}

    def register(self, module: BaseModule) -> None:
        self._modules[module.name] = module

    def get_all(self) -> list[BaseModule]:
        return list(self._modules.values())

    def setup_app(self, app: FastAPI) -> None:
        for module in self._modules.values():
            app.include_router(module.get_router())
            module.on_startup(app)

        @app.on_event("shutdown")
        async def _shutdown() -> None:
            for module in self._modules.values():
                module.on_shutdown(app)


module_registry = ModuleRegistry()
