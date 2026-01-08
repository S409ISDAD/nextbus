from fastapi import APIRouter, Depends, Request, HTTPException, Response
from backend.deps import get_redis, limiter
from backend.schemas.service import RoutePixels, Service
from backend.services import services
from backend.deps import get_logger
from backend.utils.route_matrix_display import (
    get_service_data,
    process_route,
    process_route_map,
)

router = APIRouter()


log = get_logger(__name__)


@router.get("/", response_model=Service)
@limiter.limit("45/minute")
def service_details(request: Request, service_id: int, redis=Depends(get_redis)):
    try:
        service_details = services.get_service_info(service_id, redis)

        return service_details
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/pixeldata", response_model=RoutePixels)
@limiter.limit("45/minute")
def service_pixel_data(
    request: Request,
    service_id: int,
    screen_w: int,
    screen_h: int,
    padding: int,
    redis=Depends(get_redis),
):
    try:
        service_data = get_service_data(service_id, redis)

        route_pixels = process_route(service_data, screen_w, screen_h, padding)

        return route_pixels
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/mapdata")
@limiter.limit("45/minute")
def service_map_data(
    request: Request,
    service_id: int,
    screen_w: int,
    screen_h: int,
    padding: int,
    redis=Depends(get_redis),
):
    try:
        service_data = get_service_data(service_id, redis)

        map_pixels = process_route_map(service_data, screen_w, screen_h, padding)

        return Response(
            content=bytes(map_pixels), media_type="application/octet-stream"
        )

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(500, detail="An unexpected error occurred")
