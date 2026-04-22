import asyncio
import time
from minio_config import minio_client
from scenarios import upload_docx_template
from pdf_convertion import generate_and_upload_pdf, generate_and_upload_pdf_gotenberg


async def benchmark_concurrent():
    context_data = {"name": "Concurrent", "contract_id": "999", "contractdate": "2026-04-22"}

    print("⏳ Setting up template...")
    await upload_docx_template()

    CONCURRENT_REQUESTS = 100

    print(f"\n=== Firing {CONCURRENT_REQUESTS} Manual Subprocess Requests AT THE SAME TIME ===")
    start_manual = time.perf_counter()

    manual_tasks = [generate_and_upload_pdf(f"concurrent_manual_{i}", context_data) for i in range(CONCURRENT_REQUESTS)]
    try:
        await asyncio.gather(*manual_tasks)
        manual_total_time = time.perf_counter() - start_manual
        print(f"✅ Manual Concurrent Total Time: {manual_total_time:.4f}s")
    except Exception as e:
        print(f"❌ Manual process crashed under load: {e}")

    print(f"\n=== Firing {CONCURRENT_REQUESTS} Gotenberg Requests AT THE SAME TIME ===")
    start_gotenberg = time.perf_counter()

    gotenberg_tasks = [generate_and_upload_pdf_gotenberg(f"concurrent_gotenberg_{i}", context_data) for i in
                       range(CONCURRENT_REQUESTS)]
    try:
        await asyncio.gather(*gotenberg_tasks)
        gotenberg_total_time = time.perf_counter() - start_gotenberg
        print(f"✅ Gotenberg Concurrent Total Time: {gotenberg_total_time:.4f}s")
    except Exception as e:
        print(f"❌ Gotenberg process crashed under load: {e}")

    print("\n" + "=" * 40)
    if 'manual_total_time' in locals() and 'gotenberg_total_time' in locals():
        print(f"Manual Total:    {manual_total_time:.4f}s")
        print(f"Gotenberg Total: {gotenberg_total_time:.4f}s")
    print("=" * 40)


if __name__ == "__main__":
    try:
        asyncio.run(benchmark_concurrent())
    finally:
        asyncio.run(minio_client.close_session())