import re

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .database import get_profile
from .admin import delete_record, save_record

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
templates = Jinja2Templates(directory=settings.templates_dir)

# Experience details are free text that starts with the date range, e.g.
# "Jun 2026 – Present. Conducted ...". Pull that range out so the template can
# set it in its own column; details without a leading range pass through as-is.
_LEADING_DATES = re.compile(r"^([A-Z][a-z]{2,8}\.? \d{4} [–-] (?:Present|[A-Z][a-z]{2,8}\.? \d{4}))\.?\s*(.*)$", re.S)


def split_dates(details: str) -> tuple[str, str]:
    match = _LEADING_DATES.match(details)
    return (match.group(1), match.group(2)) if match else ("", details)


templates.env.filters["split_dates"] = split_dates

@app.get("/", name="resume")
def resume(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"profile": get_profile(), "resume_available": settings.resume_pdf_path.is_file()},
    )


@app.get("/resume.pdf", name="resume_pdf")
def resume_pdf():
    profile = get_profile()
    if not settings.resume_pdf_path.is_file():
        return PlainTextResponse(
            f"The résumé PDF isn't available right now. Email {profile['email']} and I'll send it directly.",
            status_code=404,
        )
    filename = f"{profile['name'].replace(' ', '-')}-Resume.pdf"
    return FileResponse(settings.resume_pdf_path, media_type="application/pdf", filename=filename)


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
