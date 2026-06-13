import os
import logging
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

def setup_ui(app: FastAPI) -> None:
    """Mount static files and register root route for serving the integrated frontend UI."""
    # Since this file is located in src/ui/, ui_dir is the current directory src/ui/
    ui_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Mount the static files directory
    app.mount("/static", StaticFiles(directory=ui_dir), name="static")

    @app.get("/")
    async def serve_index():
        """Serve the frontend index HTML page."""
        index_path = os.path.join(ui_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        logger.warning("Frontend index.html not found at '%s'", index_path)
        return {"message": "Frontend index.html not found. Please create it under src/ui/index.html."}

    @app.get("/rules.pdf")
    async def serve_rules():
        """Serve the official MTG Comprehensive Rules PDF."""
        root_dir = os.path.dirname(os.path.dirname(ui_dir))
        pdf_path = os.path.join(root_dir, "data", "MagicCompRules 20260417.pdf")
        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf")
        logger.warning("Rules PDF not found at '%s'", pdf_path)
        return {"error": "Rules PDF not found."}
