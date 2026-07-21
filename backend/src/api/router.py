from fastapi import APIRouter

from api.routes import auth, configuracion, cotizacion, empleados, escribanos, escrituras, events, gastos_extraordinarios, impuestos, libros, liquidacion, pagos_cliente, pagos_colegio, salarios

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(escrituras.router)
api_router.include_router(gastos_extraordinarios.router)
api_router.include_router(impuestos.router)
api_router.include_router(pagos_cliente.router)
api_router.include_router(pagos_colegio.router)
api_router.include_router(events.router)
api_router.include_router(liquidacion.router)
api_router.include_router(salarios.router)
api_router.include_router(configuracion.router)
api_router.include_router(cotizacion.router)
api_router.include_router(escribanos.router)
api_router.include_router(empleados.router)
api_router.include_router(libros.router)
