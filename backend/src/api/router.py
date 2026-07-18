from fastapi import APIRouter

from api.routes import auth, configuracion, escrituras, events, gastos, liquidacion, salarios

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(escrituras.router)
api_router.include_router(gastos.router)
api_router.include_router(events.router)
api_router.include_router(liquidacion.router)
api_router.include_router(salarios.router)
api_router.include_router(configuracion.router)
