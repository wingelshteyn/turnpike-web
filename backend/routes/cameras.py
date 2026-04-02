"""Маршруты для просмотра камер (RTSP → MJPEG) с поддержкой нескольких камер.

Оптимизации:
- Фоновый поток кэширует снэпшоты → HTTP-запросы отдают из памяти мгновенно
- Не создаются новые RTSP-соединения на каждый запрос
- FPS-лимит и сжатие JPEG для потока
- Graceful shutdown потока при отключении клиента
"""

import asyncio
import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

from ..dependencies import templates

os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])

# ─── Camera registry ────────────────────────────────────────────────────────

_DEFAULT_CAMERAS = [
    {
        "id": "antichniy_skald",
        "name": "Античный скальд",
        "preview_url": "http://178.169.72.205:8082/Antichniy_skald/preview.jpg",
        "rtsp_url": "rtsp://178.169.72.205:1554/Antichniy_skald",
    },
]


def _load_cameras() -> list[dict]:
    raw = os.environ.get("CAMERAS_JSON", "")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid CAMERAS_JSON env var, falling back to defaults")
    return _DEFAULT_CAMERAS


CAMERAS: list[dict] = _load_cameras()

BOUNDARY = "frame"
EXECUTOR = ThreadPoolExecutor(max_workers=2)
MAX_STREAM_FPS = 8
SNAPSHOT_JPEG_QUALITY = 65
STREAM_JPEG_QUALITY = 60
MAX_WIDTH = 960

_cache_thread_started = False


def _find_camera(cam_id: str) -> dict | None:
    for c in CAMERAS:
        if c["id"] == cam_id:
            return c
    return None


# ─── Snapshot cache ──────────────────────────────────────────────────────────

_cache: dict[str, bytes] = {}
_cache_lock = threading.Lock()
_cache_refresh_interval = 8.0


def _fetch_http_preview(url: str) -> bytes | None:
    """Синхронный HTTP-запрос для превью (используется в фоновом потоке)."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = resp.read()
                if data and len(data) > 100:
                    return data
    except Exception:
        pass
    return None


def _read_frame_opencv(rtsp_url: str, transport: str = "tcp") -> bytes | None:
    import cv2

    prev = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS")
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{transport}"
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        try:
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                if w > MAX_WIDTH:
                    scale = MAX_WIDTH / w
                    frame = cv2.resize(frame, (MAX_WIDTH, int(h * scale)),
                                       interpolation=cv2.INTER_AREA)
                _, jpeg = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, SNAPSHOT_JPEG_QUALITY],
                )
                if jpeg is not None:
                    return jpeg.tobytes()
        finally:
            cap.release()
    finally:
        if prev is not None:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = prev
        else:
            os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)
    return None


def _read_frame_ffmpeg(rtsp_url: str, transport: str = "tcp") -> bytes | None:
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-rtsp_transport", transport,
                "-i", rtsp_url,
                "-vf", f"scale={MAX_WIDTH}:-1",
                "-vframes", "1",
                "-f", "image2", "-vcodec", "mjpeg",
                "-q:v", "10",
                "pipe:1",
            ],
            capture_output=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout:
            data = result.stdout
            start = data.find(b"\xff\xd8")
            end = data.find(b"\xff\xd9", start)
            if start >= 0 and end > start:
                return data[start:end + 2]
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("ffmpeg fallback: %s", e)
    return None


def _capture_snapshot(cam: dict) -> bytes | None:
    """Захват одного кадра: HTTP preview → RTSP OpenCV → RTSP ffmpeg."""
    preview_url = cam.get("preview_url", "")
    if preview_url:
        data = _fetch_http_preview(preview_url)
        if data:
            return data

    rtsp_url = cam.get("rtsp_url", "")
    if not rtsp_url:
        return None

    for transport in ("tcp", "udp"):
        out = _read_frame_opencv(rtsp_url, transport)
        if out is not None:
            return out
    for transport in ("tcp", "udp"):
        out = _read_frame_ffmpeg(rtsp_url, transport)
        if out is not None:
            return out
    return None


def _cache_worker():
    """Фоновый поток: обновляет кэш снэпшотов для всех камер последовательно."""
    logger.info("Snapshot cache worker started (%d cameras, interval %.0fs)",
                len(CAMERAS), _cache_refresh_interval)
    while True:
        for cam in CAMERAS:
            try:
                jpeg = _capture_snapshot(cam)
                if jpeg:
                    with _cache_lock:
                        _cache[cam["id"]] = jpeg
            except Exception as e:
                logger.warning("Cache refresh error for %s: %s", cam["id"], e)
        time.sleep(_cache_refresh_interval)


def _ensure_cache_thread_started() -> None:
    global _cache_thread_started
    if _cache_thread_started:
        return
    _cache_thread_started = True
    thread = threading.Thread(target=_cache_worker, daemon=True)
    thread.start()


def _get_cached_snapshot(cam_id: str) -> bytes | None:
    with _cache_lock:
        return _cache.get(cam_id)


# ─── MJPEG stream ───────────────────────────────────────────────────────────


async def _generate_mjpeg(rtsp_url: str):
    """MJPEG-поток с FPS-лимитом и graceful shutdown."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue(maxsize=2)
    stop_event = threading.Event()
    target_interval = 1.0 / MAX_STREAM_FPS

    def producer():
        import cv2

        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        try:
            while not stop_event.is_set():
                t0 = time.monotonic()
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)),
                                       interpolation=cv2.INTER_AREA)
                _, jpeg = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, STREAM_JPEG_QUALITY],
                )
                if jpeg is not None and len(jpeg) > 0:
                    try:
                        loop.call_soon_threadsafe(queue.put_nowait, jpeg.tobytes())
                    except asyncio.QueueFull:
                        pass
                elapsed = time.monotonic() - t0
                if elapsed < target_interval:
                    time.sleep(target_interval - elapsed)
        except Exception as e:
            logger.warning("Stream capture error: %s", e)
        finally:
            cap.release()
            try:
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except RuntimeError:
                pass

    thread = threading.Thread(target=producer, daemon=True)
    thread.start()

    try:
        while True:
            data = await queue.get()
            if data is None:
                break
            yield (
                f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n\r\n".encode()
                + data + b"\r\n"
            )
    except (asyncio.CancelledError, GeneratorExit):
        pass
    finally:
        stop_event.set()


# ─── JSON API ────────────────────────────────────────────────────────────────


@router.get("/api/list")
async def api_cameras_list():
    return JSONResponse([{"id": c["id"], "name": c["name"]} for c in CAMERAS])


@router.get("/api/{cam_id}/snapshot")
async def api_camera_snapshot(cam_id: str):
    _ensure_cache_thread_started()
    cam = _find_camera(cam_id)
    if not cam:
        return Response(status_code=404, content=b"Camera not found")

    cached = _get_cached_snapshot(cam_id)
    if cached:
        return Response(
            content=cached,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3", "X-Source": "cache"},
        )

    # Кэш ещё не заполнен — единоразовый захват (только при первом запросе)
    jpeg = await asyncio.get_event_loop().run_in_executor(
        EXECUTOR, _capture_snapshot, cam,
    )
    if jpeg:
        with _cache_lock:
            _cache[cam_id] = jpeg
        return Response(
            content=jpeg,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache, no-store", "X-Source": "live"},
        )

    return Response(status_code=503, content=b"Stream unavailable")


@router.get("/api/{cam_id}/stream")
async def api_camera_stream(cam_id: str):
    _ensure_cache_thread_started()
    cam = _find_camera(cam_id)
    if not cam:
        return Response(status_code=404, content=b"Camera not found")

    rtsp_url = cam.get("rtsp_url", "")
    if not rtsp_url:
        return Response(status_code=503, content=b"No RTSP URL configured")

    return StreamingResponse(
        _generate_mjpeg(rtsp_url),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# ─── Legacy endpoints ────────────────────────────────────────────────────────


@router.get("/stream")
async def cameras_stream():
    if CAMERAS:
        return await api_camera_stream(CAMERAS[0]["id"])
    return Response(status_code=503, content=b"No cameras configured")


@router.get("/snapshot")
async def cameras_snapshot():
    if CAMERAS:
        return await api_camera_snapshot(CAMERAS[0]["id"])
    return Response(status_code=503, content=b"No cameras configured")


# ─── Page ─────────────────────────────────────────────────────────────────────


@router.get("", response_class=HTMLResponse)
async def cameras_page(request: Request):
    safe_cameras = [{"id": c["id"], "name": c["name"]} for c in CAMERAS]
    return templates.TemplateResponse(
        "cameras/index.html",
        {"request": request, "cameras": safe_cameras},
    )
