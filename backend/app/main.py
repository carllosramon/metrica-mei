from fastapi import FastAPI

from app.controllers.auth_controller import router as auth_router


app = FastAPI(
    title="MetricaMEI API",
    version="0.2.0",
)

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}