from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .database import get_profile

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
