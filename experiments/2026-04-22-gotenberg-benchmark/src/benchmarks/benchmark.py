import asyncio
import time
import statistics

from minio_config import minio_client
from scenarios import upload_docx_template
from pdf_convertion import generate_and_upload_pdf, generate_and_upload_pdf_gotenberg


async def benchmark():
    context_data = {
        "name": "Benchmark Tester",
        "contract_id": "7777777",
        "contractdate": "16 апреля 2026 г."
    }

    print("⏳ Setting up template in MinIO...")
    try:
        await upload_docx_template()
    except Exception as e:
        print(f"❌ Setup failed (check if MinIO is running): {e}")
        return
    print("✅ Setup complete.\n")

    ITERATIONS = 10

    print(f"=== Running Manual Subprocess Benchmarks ({ITERATIONS} iterations) ===")
    manual_times = []
    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            await generate_and_upload_pdf(f"manual_test_{i}", context_data)
            elapsed = time.perf_counter() - start
            manual_times.append(elapsed)
            print(f"Iteration {i + 1}: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Manual iteration {i + 1} failed: {e}")

    print(f"\n=== Running Gotenberg Benchmarks ({ITERATIONS} iterations) ===")
    gotenberg_times = []
    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            await generate_and_upload_pdf_gotenberg(f"gotenberg_test_{i}", context_data)
            elapsed = time.perf_counter() - start
            gotenberg_times.append(elapsed)
            print(f"Iteration {i + 1}: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Gotenberg iteration {i + 1} failed: {e}")

    print("\n" + "=" * 40)
    print("📊 BENCHMARK RESULTS SUMMARY")
    print("=" * 40)

    if manual_times:
        avg_manual = statistics.mean(manual_times)
        print(f"Manual (Subprocess) Average: {avg_manual:.4f}s")

    if gotenberg_times:
        avg_gotenberg = statistics.mean(gotenberg_times)
        print(f"Gotenberg (API) Average:     {avg_gotenberg:.4f}s")

    if manual_times and gotenberg_times:
        speedup = avg_manual / avg_gotenberg
        diff = avg_manual - avg_gotenberg
        print("-" * 40)
        if speedup > 1:
            print(f"🚀 Gotenberg is {speedup:.2f}x faster (saves ~{diff:.4f}s per file)")
        else:
            print(f"🐢 Manual is {1 / speedup:.2f}x faster")
    print("=" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(benchmark())
    finally:
        asyncio.run(minio_client.close_session())