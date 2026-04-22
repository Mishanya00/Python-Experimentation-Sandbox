import time
import asyncio
import statistics

from pdf_convertion import (
    convert_pure_file_manual,
    convert_pure_file_gotenberg,
)


async def main():
    ITERATIONS = 3
    s_obj = 'huge_document.docx'
    s_bucket = 'pdf-generation'
    d_bucket = 'documents'

    print('=== Manual pure PDF creation ===')
    manual_times = []

    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            await convert_pure_file_manual(s_bucket, s_obj, d_bucket, f'pure_manual_{i}')
            elapsed = time.perf_counter() - start
            manual_times.append(elapsed)
            print(f"Iteration {i + 1}: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Gotenberg iteration {i + 1} failed: {e}")

    print('=== Gotenberg PDF creation ===')
    gotenberg_times = []

    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            await convert_pure_file_gotenberg(s_bucket, s_obj, d_bucket, f'pure_goten_{i}')
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
    asyncio.run(main())