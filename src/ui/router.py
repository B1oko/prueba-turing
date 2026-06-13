import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
        return {"message": "Frontend index.html not found. Please create it under src/ui/index.html."}
