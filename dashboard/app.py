
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv(
    "TRACELENS_API_URL",
    "http://127.0.0.1:8000",
)

st.set_page_config(
    page_title="TraceLens",
    page_icon="🔍",
    layout="wide",
)

st.title("TraceLens")
st.caption("AI Application Debugger & Observability Dashboard")


st.subheader("Run an AI Workflow")

with st.form("run_workflow_form"):
    question = st.text_area(
        "Enter your question",
        value="Explain how an AI application works",
        max_chars=2000,
    )

    mode = st.radio(
        "Execution mode",
        ["Simulated", "Real AI (Groq)"],
        horizontal=True,
    )

    simulate_failure = st.checkbox(
        "Simulate retrieval failure (testing only)"
    )

    submitted = st.form_submit_button("Run workflow")

if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/demo/run",
                params={
                    "question": question.strip(),
                    "simulate_failure": simulate_failure,
                    "use_groq": mode == "Real AI (Groq)",
                },
                timeout=45,
            )
            response.raise_for_status()
            result = response.json()

            st.subheader("Workflow Result")
            st.write("**Status:**", result["status"])
            st.write("**Model:**", result["model"])
            st.write("**Latency:**", f'{result["latency_ms"]:.2f} ms')
            st.write(
                "**Tokens:**",
                f'{result["input_tokens"]} input + '
                f'{result["output_tokens"]} output',
            )

            if result.get("output"):
                st.markdown("### AI Answer")
                st.markdown(result["output"])
            else:
                st.warning("No answer was generated.")

            with st.expander("View execution trace"):
                st.json(result)

        except requests.RequestException as exc:
            st.error(f"Workflow request failed: {exc}")


if st.button("Refresh traces"):
    st.rerun()

try:
    response = requests.get(
        f"{API_URL}/traces",
        timeout=10,
    )
    response.raise_for_status()
    records = response.json()["traces"]

except requests.RequestException as exc:
    st.error(f"Could not load traces: {exc}")
    st.stop()

if not records:
    st.info("No traces found. Run a demo workflow first.")
    st.stop()

df = pd.DataFrame(records)

total = len(df)
failed = int((df["status"] == "failed").sum())
success = total - failed
failure_rate = failed / total * 100
avg_latency = float(df["latency_ms"].mean())

st.subheader("Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Runs", total)
col2.metric("Successful Runs", success)
col3.metric("Failed Runs", failed)
col4.metric("Failure Rate", f"{failure_rate:.1f}%")
col5.metric("Average Latency", f"{avg_latency:.2f} ms")



st.subheader("Trace Latency Comparison")

latency_chart_data = df[["trace_id", "latency_ms"]].copy()
latency_chart_data["trace_id"] = (
    latency_chart_data["trace_id"].str.slice(0, 8)
)

st.bar_chart(
    latency_chart_data,
    x="trace_id",
    y="latency_ms",
)

st.subheader("Trace Latency Comparison")

latency_chart_data = df[["trace_id", "latency_ms"]].copy()
latency_chart_data["trace_id"] = (
    latency_chart_data["trace_id"].str.slice(0, 8)
)

st.bar_chart(
    latency_chart_data,
    x="trace_id",
    y="latency_ms",
)


st.subheader("All Traces")

search_text = st.text_input(
    "Search by question or trace ID"
)

status_filter = st.selectbox(
    "Filter by status",
    ["All", "success", "failed"],
)

filtered_df = df.copy()

if search_text:
    matches = (
        filtered_df["question"].str.contains(
            search_text, case=False, na=False, regex=False
        )
        | filtered_df["trace_id"].str.contains(
            search_text, case=False, na=False, regex=False
        )
    )
    filtered_df = filtered_df[matches]

if status_filter != "All":
    filtered_df = filtered_df[
        filtered_df["status"] == status_filter
    ]

columns = ["trace_id", "question", "status", "latency_ms", "model"]

st.dataframe(
    filtered_df[columns],
    use_container_width=True,
    hide_index=True,
)

st.caption(f"Showing {len(filtered_df)} of {len(df)} traces")


st.subheader("Inspect a Trace")

# Let the user choose which records to inspect
available_records = filtered_df.to_dict(orient="records")

if not available_records:
    st.info("No failed traces found.")
    st.stop()

selected_id = st.selectbox(
    "Select a trace ID",
    [item["trace_id"] for item in available_records],
)

selected_trace = next(
    item for item in available_records
    if item["trace_id"] == selected_id
)

# Overall trace details
st.write("**Question:**", selected_trace["question"])
st.write("**Overall status:**", selected_trace["status"])
st.write("**Total latency:**", f"{selected_trace['latency_ms']:.2f} ms")

# Inspect every execution step

st.subheader("Execution Step Duration")

steps_df = pd.DataFrame(selected_trace.get("steps", []))

if not steps_df.empty:
    st.bar_chart(
        steps_df,
        x="name",
        y="duration_ms",
    )
else:
    st.info("No execution steps recorded.")

st.subheader("Execution Steps")

for step in selected_trace.get("steps", []):
    with st.expander(
        f"{step['name']} — {step['status'].upper()}"
    ):
        st.write("Duration:", f"{step['duration_ms']:.2f} ms")

        if step.get("error"):
            st.error(f"Error: {step['error']}")
        else:
            st.success("No error recorded.")

# Show the full stored record
with st.expander("View raw trace JSON"):
    st.json(selected_trace)
