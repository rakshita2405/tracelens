
from fastapi import FastAPI, HTTPException
from pymongo.errors import DuplicateKeyError, PyMongoError
from fastapi import Query
from app.demo_ai import run_demo
from app.database import database
from app.schemas import TraceCreate

app = FastAPI(title="TraceLens API")

traces = database["traces"]
traces.create_index("trace_id", unique=True)


@app.get("/")
def home():
    return {"message": "Welcome to TraceLens"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TraceLens"}


@app.post("/traces", status_code=201)
def create_trace(trace: TraceCreate):
    document = trace.model_dump()

    try:
        traces.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Trace ID already exists",
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed",
        )

    return {"message": "Trace saved", "trace_id": trace.trace_id}


@app.get("/traces/{trace_id}")
def get_trace(trace_id: str):
    try:
        trace = traces.find_one(
            {"trace_id": trace_id},
            {"_id": 0},
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed",
        )

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace



@app.get("/traces")
def list_traces(limit: int = 50):
    limit = max(1, min(limit, 100))

    try:
        results = list(
            traces.find({}, {"_id": 0})
            .sort("trace_id", -1)
            .limit(limit)
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed",
        )

    return {
        "traces": results,
        "count": len(results),
    }


@app.post("/demo/run")
def demo_run(
    question: str = Query(
        default="Explain how an AI application works",
        min_length=1,
        max_length=2000,
    ),
    simulate_failure: bool = False,
    use_groq: bool = False,
):
    result = run_demo(
        question=question,
        simulate_failure=simulate_failure,
        use_groq=use_groq,
    )

    trace = {key: value for key, value in result.items() if key != "output"}

    try:
        traces.insert_one(trace)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Trace ID already exists",
        )
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Database temporarily unavailable",
        )

    return result
