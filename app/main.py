import sys
import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.settings import settings
from app.database import Base, engine, SessionLocal
from app import models
from app.routers import orders, inventory


# LOGGING CONFIG
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<yellow>trace={extra[trace_id]}</yellow> | "
    "<level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """redirect stdlib logging → loguru"""
    def emit(self, record):
        logger.opt(
            depth=6,
            exception=record.exc_info
        ).log(record.levelname, record.getMessage())


def setup_logging():
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        colorize=True,
        format=LOG_FORMAT,
        enqueue=True,
    )

    logger.add(
        "logs/app.log",
        level=settings.log_level.upper(),
        rotation="1 day",
        retention="7 days",
        compression="zip",
        format=LOG_FORMAT,
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


setup_logging()


# FASTAPI APP
app = FastAPI(
    title=settings.app_name,
    description="order placement + validation + inventory system",
    version=settings.app_version,
    debug=settings.debug,
)



# VALIDATION ERROR HANDLER

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace = getattr(request.state, "trace_id", "validation")
    logger.bind(trace_id=trace).warning("validation error")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": "validation_error",
            "message": "invalid request payload",
            "errors": exc.errors(),
        },
    )



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)



# DB INIT

Base.metadata.create_all(bind=engine)



def seed_inventory():
    db = SessionLocal()
    try:
        existing = {x.sku for x in db.query(models.Inventory).all()}
        furniture_items = [
                ("FUR001", "Wooden Chair", 30),
                ("FUR002", "Office Chair", 60),
                ("FUR003", "Recliner Chair", 40),
                ("FUR004", "Dining Table", 16),
                ("FUR005", "Coffee Table", 36),
                ("FUR006", "Side Table", 40),
                ("FUR007", "Study Desk", 24),
                ("FUR008", "Office Desk", 20),
                ("FUR009", "Bookshelf", 28),
                ("FUR010", "Wardrobe", 18),
                ("FUR011", "Sofa 2-Seater", 14),
                ("FUR012", "Sofa 3-Seater", 12),
                ("FUR013", "L-Shaped Sofa", 10),
                ("FUR014", "TV Unit", 26),
                ("FUR015", "TV Cabinet", 20),
                ("FUR016", "Bed Queen Size", 16),
                ("FUR017", "Bed King Size", 12),
                ("FUR018", "Bed Single", 20),
                ("FUR019", "Bedside Table", 40),
                ("FUR020", "Shoe Rack", 32),
                ("FUR027", "Folding Chair", 60),
                ("FUR040", "Dining Bench", 24),
                ("FUR080", "Reclining Sofa", 10),
                ("FUR120", "Extendable Dining Table", 8),

                # New Items
                # Chairs
                ("FUR021", "Bar Stool", 25),
                ("FUR022", "Armchair", 15),
                ("FUR023", "Rocking Chair", 12),
                ("FUR024", "Bean Bag Chair", 20),
                ("FUR025", "Gaming Chair", 10),
                ("FUR026", "Director's Chair", 8),
                ("FUR028", "Wingback Chair", 7),
                ("FUR029", "Lounge Chair", 9),
                ("FUR030", "Dining Chair", 35),

                # Tables
                ("FUR031", "Console Table", 14),
                ("FUR032", "Accent Table", 18),
                ("FUR033", "Nesting Tables", 12),
                ("FUR034", "Outdoor Table", 10),
                ("FUR035", "Folding Table", 22),
                ("FUR036", "Computer Desk", 16),
                ("FUR037", "Writing Desk", 11),
                ("FUR038", "Corner Desk", 9),
                ("FUR039", "Standing Desk", 8),

                # Sofas
                ("FUR041", "Sectional Sofa", 6),
                ("FUR042", "Loveseat", 10),
                ("FUR043", "Chaise Lounge", 5),
                ("FUR044", "Convertible Sofa", 7),
                ("FUR045", "Futon", 12),
                ("FUR046", "Sleeper Sofa", 4),
                ("FUR047", "Chesterfield Sofa", 3),
                ("FUR048", "Mid-Century Sofa", 6),

                # Beds
                ("FUR049", "Bunk Bed", 5),
                ("FUR050", "Trundle Bed", 4),
                ("FUR051", "Canopy Bed", 3),
                ("FUR052", "Platform Bed", 10),
                ("FUR053", "Adjustable Bed", 6),
                ("FUR054", "Daybed", 7),
                ("FUR055", "Murphy Bed", 2),
                ("FUR056", "Four-Poster Bed", 4),

                # Storage
                ("FUR057", "Chest of Drawers", 12),
                ("FUR058", "Dresser", 15),
                ("FUR059", "Nightstand", 20),
                ("FUR060", "Entertainment Center", 8),
                ("FUR061", "Storage Ottoman", 14),
                ("FUR062", "Bookcase", 18),
                ("FUR063", "Sideboard", 10),
                ("FUR064", "Cabinet", 11),
                ("FUR065", "Wine Rack", 7),

                # Outdoor
                ("FUR066", "Patio Chair", 16),
                ("FUR067", "Outdoor Sofa", 5),
                ("FUR068", "Hammock", 8),
                ("FUR069", "Picnic Table", 6),
                ("FUR070", "Adirondack Chair", 12),
                ("FUR071", "Outdoor Bench", 10),
                ("FUR072", "Sun Lounger", 9),

                # Kids
                ("FUR073", "Kids Bed", 8),
                ("FUR074", "Kids Chair", 15),
                ("FUR075", "Kids Table", 12),
                ("FUR076", "Toy Chest", 10),
                ("FUR077", "Bunk Bed with Desk", 4),
                ("FUR078", "Kids Bookshelf", 14),

                # Office
                ("FUR079", "Executive Chair", 10),
                ("FUR081", "Conference Table", 3),
                ("FUR082", "Filing Cabinet", 8),
                ("FUR083", "Desk Organizer", 20),
                ("FUR084", "Whiteboard", 7),

                # Miscellaneous
                ("FUR085", "Room Divider", 5),
                ("FUR086", "Mirror", 12),
                ("FUR087", "Wall Shelf", 18),
                ("FUR088", "Coat Rack", 10),
                ("FUR089", "Ladder Shelf", 6),
                ("FUR090", "Floating Shelf", 15),
                ("FUR091", "Bar Cart", 8),
                ("FUR092", "TV Stand", 11),
                ("FUR093", "Magazine Rack", 9),
                ("FUR094", "Plant Stand", 14),
                ("FUR095", "Stool", 20),
                ("FUR096", "Foldable Desk", 12),
                ("FUR097", "Wall-Mounted Desk", 7),
                ("FUR098", "Corner Shelf", 10),
                ("FUR099", "Underbed Storage", 8),
                ("FUR100", "Jewelry Armoire", 5),
                ("FUR101", "Shoe Cabinet", 11),
                ("FUR102", "Hat Stand", 6),
                ("FUR103", "Umbrella Stand", 9),
                ("FUR104", "Pet Bed", 15),
                ("FUR105", "Pet House", 7),
                ("FUR106", "Kitchen Island", 4),
                ("FUR107", "Breakfast Bar", 6),
                ("FUR108", "Wet Bar", 3),
                ("FUR109", "Vanity", 8),
                ("FUR110", "Medicine Cabinet", 10),
                ("FUR111", "Linen Cabinet", 7),
                ("FUR112", "Spice Rack", 12),
                ("FUR113", "Cutlery Organizer", 15),
                ("FUR114", "Kitchen Cart", 9),
                ("FUR115", "Bakers Rack", 6),
                ("FUR116", "Pantry Cabinet", 5),
                ("FUR117", "Wine Cabinet", 4),
                ("FUR118", "Display Cabinet", 8),
                ("FUR119", "Curio Cabinet", 3),
    ]


        new_items = [
            models.Inventory(sku=sku, name=name, stock=stock)
            for sku, name, stock in furniture_items
            if sku not in existing
        ]

        if new_items:
            db.add_all(new_items)
            db.commit()
            logger.bind(trace_id="startup").success(
                f"seeded {len(new_items)} inventory items"
            )
        else:
            logger.bind(trace_id="startup").info("inventory already seeded — skipping")

    except Exception:
        db.rollback()
        logger.bind(trace_id="startup").exception("error seeding inventory")
    finally:
        db.close()

seed_inventory()



# TRACE-ID MIDDLEWARE

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    log = logger.bind(trace_id=trace_id)

    start = time.time()
    log.info(f"req | {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception:
        log.exception(f"unhandled | {request.method} {request.url.path}")
        raise

    duration = round((time.time() - start) * 1000, 2)

    log.info(
        f"res | {request.method} {request.url.path} "
        f"| status={response.status_code} | {duration}ms"
    )

    response.headers["x-trace-id"] = trace_id
    return response


# EVENTS
@app.on_event("startup")
async def startup_event():
    logger.bind(trace_id="startup").info("api started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.bind(trace_id="shutdown").info("api stopped")



# ROUTERS
app.include_router(orders.router)      # user endpoints
app.include_router(inventory.router)   # admin endpoints


# BASIC ROUTES
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} running",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# DEV MODE
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )