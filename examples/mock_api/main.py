from fastapi import FastAPI
from routes import all_routers

app = FastAPI(
    title="Mock Laboratory API",
    description="Mock laboratory instrument and measurement API for SiLA2 conversion examples",
    version="0.1.0",
)


for router in all_routers():
    app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint

    Returns:
        Status information
    """

    return {"status": "ok", "service": "mock-laboratory-api"}


if __name__ == "__main__":
    from pathlib import Path

    import uvicorn

    mock_api_dir = Path(__file__).parent

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(mock_api_dir)],
    )
