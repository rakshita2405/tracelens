
import os
import time
import uuid

from dotenv import load_dotenv
from groq import Groq, APIError


load_dotenv()


def run_demo(
    question: str,
    simulate_failure: bool = False,
    use_groq: bool = False,
):
    start = time.perf_counter()
    steps = []
    output = None
    input_tokens = 0
    output_tokens = 0
    model = "simulated-model"

    # Step 1: Simulate document retrieval.
    retrieval_start = time.perf_counter()

    if simulate_failure:
        retrieval_status = "failed"
        retrieval_error = "No relevant document found"
    else:
        retrieval_status = "success"
        retrieval_error = None

    steps.append({
        "name": "retrieval",
        "status": retrieval_status,
        "duration_ms": round(
            (time.perf_counter() - retrieval_start) * 1000, 2
        ),
        "error": retrieval_error,
    })

    # Step 2: Generate an answer only if retrieval succeeds.
    if retrieval_status == "failed":
        final_status = "failed"

    else:
        llm_start = time.perf_counter()

        if use_groq:
            try:
                api_key = os.getenv("GROQ_API_KEY")

                if not api_key:
                    raise RuntimeError(
                        "GROQ_API_KEY is missing from the environment"
                    )

                model = "openai/gpt-oss-20b"
                client = Groq(
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=0,
                )

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the AI assistant inside TraceLens. "
                                "Answer the user's question clearly and "
                                "concisely."
                            ),
                        },
                        {
                            "role": "user",
                            "content": question,
                        },
                    ],
                )

                output = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                final_status = "success"
                llm_error = None

            except (APIError, RuntimeError) as exc:
                final_status = "failed"
                llm_error = (
                    f"Groq request failed: {type(exc).__name__}"
                )

        else:
            output = f"Simulated answer to: {question}"
            final_status = "success"
            llm_error = None

        steps.append({
            "name": "llm",
            "status": final_status,
            "duration_ms": round(
                (time.perf_counter() - llm_start) * 1000, 2
            ),
            "error": llm_error,
        })

    trace = {
        "trace_id": str(uuid.uuid4()),
        "question": question,
        "status": final_status,
        "steps": steps,
        "latency_ms": round(
            (time.perf_counter() - start) * 1000, 2
        ),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": model,
    }

    return {**trace, "output": output}
