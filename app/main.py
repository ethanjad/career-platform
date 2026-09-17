from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .database import get_profile
from .admin import delete_record, save_record

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
templates = Jinja2Templates(directory=settings.templates_dir)

@app.get("/", name="resume")
def resume(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"profile": get_profile()},
    )


def require_admin(secret: str | None) -> None:
    if secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Invalid admin secret")


@app.post("/admin/{table}")
def create_admin_record(table: str, payload: dict, x_admin_secret: str | None = Header(default=None)):
    require_admin(x_admin_secret)
    save_record(table, payload)
    return {"ok": True}


@app.put("/admin/{table}/{record_id}")
def update_admin_record(table: str, record_id: int, payload: dict, x_admin_secret: str | None = Header(default=None)):
    require_admin(x_admin_secret)
    save_record(table, payload, record_id)
    return {"ok": True}


@app.delete("/admin/{table}/{record_id}")
def remove_admin_record(table: str, record_id: int, x_admin_secret: str | None = Header(default=None)):
    require_admin(x_admin_secret)
    delete_record(table, record_id)
    return {"ok": True}
