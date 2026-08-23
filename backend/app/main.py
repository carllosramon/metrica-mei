from fastapi import FastAPI

from app.controllers.auth_controller import router as auth_router
from app.controllers.content_controller import router as content_router


app = FastAPI(
    title="MetricaMEI API",
    version="0.2.0",
)

app.include_router(auth_router)
app.include_router(content_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
