from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.content_controller import router as content_router
from app.controllers.dashboard_controller import (
    router as dashboard_router,
)
from app.controllers.metric_controller import (
    router as metric_router,
)


app = FastAPI(
    title="MetricaMEI API",
    version="0.7.0",
)

# O frontend roda em outra porta durante o desenvolvimento, então o
# navegador trata cada requisição como origem cruzada e a bloqueia
# sem esta liberação explícita.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins(),
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)

app.include_router(auth_router)
app.include_router(content_router)
app.include_router(metric_router)
app.include_router(dashboard_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
