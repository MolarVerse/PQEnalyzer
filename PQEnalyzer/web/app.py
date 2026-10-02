"""
Local HTTP server for the PQEnalyzer web front end.

Run with ``pqenalyzer web FILE [FILE ...]``. Binds to loopback only, like
PQViewer: no authentication, do not expose to untrusted networks.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from socket import AF_INET, AF_INET6, create_server
from threading import Timer
import webbrowser

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766


def create_app(filenames, input_format="auto", reader=None):
    """
    Build the FastAPI application for already-validated input files.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from fastapi.staticfiles import StaticFiles

    from ..readers import create_reader
    from .api import WebState

    state = WebState(
        reader if reader is not None
        else create_reader(filenames, input_format))

    @asynccontextmanager
    async def lifespan(_application):
        try:
            yield
        finally:
            state.close()

    application = FastAPI(title="PQEnalyzer Web", lifespan=lifespan)
    application.state.web_state = state

    @application.middleware("http")
    async def no_store_api_responses(request, call_next):
        """
        Live-monitoring data must never be served from an HTTP cache.
        """
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/api/meta")
    def get_meta():
        return state.meta()

    @application.get("/api/status")
    def get_status():
        return state.status()

    @application.post("/api/refresh")
    def post_refresh():
        try:
            return state.refresh()
        except Exception as error:  # pylint: disable=broad-exception-caught
            raise HTTPException(status_code=500, detail=str(error))

    @application.get("/api/events")
    def get_events():
        """
        Live staleness pushes (text/event-stream). The manual path stays
        POST /api/refresh; GET /api/status stays the poll fallback.
        """
        return StreamingResponse(
            state.events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "X-Accel-Buffering": "no",
            },
        )

    @application.get("/api/parameters")
    def get_parameters():
        return state.parameters()

    @application.get("/api/series")
    def get_series(parameter: str, max_points: int = 4000):
        try:
            return state.series(parameter, max_points=max_points)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error))

    @application.get("/api/overlays")
    def get_overlays(
        parameter: str,
        mean: bool = False,
        median: bool = False,
        cumulative_average: bool = False,
        # Compatibility for clients released before the spelling was fixed.
        cummulative_average: bool = False,
        autocorrelation: bool = False,
        running_average: bool = False,
        window_size: str = "",
    ):
        try:
            return state.overlays(parameter, {
                "mean": mean,
                "median": median,
                "cumulative_average": (
                    cumulative_average or cummulative_average
                ),
                "autocorrelation": autocorrelation,
                "running_average": running_average,
            }, window_size=window_size)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))

    @application.get("/api/histogram")
    def get_histogram(parameter: str, bins: str = "auto"):
        try:
            return state.histogram(parameter, bins=bins)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))

    @application.get("/api/summary")
    def get_summary(parameter: str):
        try:
            return state.summary(parameter)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error))

    @application.get("/api/summaries")
    def get_summaries():
        return state.summaries()

    if STATIC_DIR.is_dir():
        application.mount(
            "/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    else:
        @application.get("/")
        def missing_frontend():
            raise HTTPException(
                status_code=404,
                detail="Web frontend not built yet: run "
                "`npm --prefix PQEnalyzer/PQEnalyzer/web/frontend run build`.",
            )

    return application


def serve(filenames, input_format="auto", host=DEFAULT_HOST, port=DEFAULT_PORT,
          open_browser=True, reader=None):
    """
    Validate inputs, then serve the web front end on loopback.
    """
    import uvicorn

    from ..readers import create_reader

    if reader is None:
        try:
            reader = create_reader(filenames, input_format)
        except Exception as error:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Could not open source: {error}")

    url_host = f"[{host}]" if ":" in host else host
    url = f"http://{url_host}:{port}"
    try:
        listener = create_server(
            (host, port), family=AF_INET6 if ":" in host else AF_INET)
    except OSError as error:
        raise ValueError(
            f"Could not start Web server at {url}: {error}. "
            "Choose another --port.") from error
    with listener:
        application = create_app(filenames, input_format, reader=reader)
        print(f"PQEnalyzer Web: {url}", flush=True)
        if open_browser:
            _open_browser_later(url)

        class StreamingServer(uvicorn.Server):
            """Close live streams before Uvicorn waits for connections."""

            async def shutdown(self, sockets=None):
                application.state.web_state.close()
                await super().shutdown(sockets=sockets)

        config = uvicorn.Config(
            application, host=host, port=port, reload=False)
        StreamingServer(config).run(sockets=[listener])


def _open_browser_later(url):
    """
    Open the browser shortly after startup without blocking the server.
    """
    timer = Timer(0.75, webbrowser.open, args=(url,))
    timer.daemon = True
    timer.start()
