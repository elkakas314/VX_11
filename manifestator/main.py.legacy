from fastapi import FastAPI

app = FastAPI(title="VX11 Manifestator (Legacy)")


@app.get("/health")
def health():
    return {"status": "ok", "module": "manifestator", "legacy": True}

