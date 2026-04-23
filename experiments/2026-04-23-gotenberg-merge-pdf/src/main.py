import asyncio
import time
import statistics

from minio_config import minio_client, FILES_DIR
from minio_service import MinioService
from pdf_converter_manual import PDFConverterManual
from pdf_converter_gotenberg import PDFConverterGotenberg


async def benchmark(storage_service: MinioService, gotenberg_converter: PDFConverterGotenberg):
    # pdf_2 = await gotenberg_converter.generate_pdf_bytes("static.docx", None)

    context_data = {
        "name": "Gorro", 
        "age": "Maakintosh", 
        "description": "Consistency lorem ipsum",
    }

    print("⏳ Setting up template in MinIO...")

    ITERATIONS = 10

    print(f"=== Without pdf merge ===")
    deltas_1 = []
    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()
            await gotenberg_converter.generate_and_upload_pdf("full.docx", f"no_merge_test_{i}", context_data)
            elapsed = time.perf_counter() - start
            deltas_1.append(elapsed)
            print(f"Iteration {i + 1}: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Iteration {i + 1} failed: {e}")

    print(f"\n=== With pdf merge ===")
    deltas_2 = []
    for i in range(ITERATIONS):
        try:
            start = time.perf_counter()

            pdf_1 = await gotenberg_converter.generate_pdf_bytes("first_page.docx", context_data)

            pdf_2 = await storage_service.download_to_ram('templates', 'static.pdf')

            full = await gotenberg_converter.merge_pdfs([pdf_1, pdf_2])

            await storage_service.upload_bytes('documents', f'full_merged_{i}.pdf', full)

            elapsed = time.perf_counter() - start
            deltas_2.append(elapsed)
            print(f"Iteration {i + 1}: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Iteration {i + 1} failed: {e}")

    print("\n" + "=" * 40)
    print("📊 BENCHMARK RESULTS SUMMARY")
    print("=" * 40)

    if deltas_1:
        avg_manual = statistics.mean(deltas_1)
        print(f"Not merge: {avg_manual:.4f}s")

    if deltas_2:
        avg_gotenberg = statistics.mean(deltas_2)
        print(f"PDF Merge:     {avg_gotenberg:.4f}s")

    if deltas_1 and deltas_2:
        speedup = avg_manual / avg_gotenberg
        diff = avg_manual - avg_gotenberg
        print("-" * 40)
        if speedup > 1:
            print(f"🚀 Merge is {speedup:.2f}x faster (saves ~{diff:.4f}s per file)")
        else:
            print(f"🐢 No merge is {1 / speedup:.2f}x faster")
    print("=" * 40)


async def main():
    storage_service = MinioService(minio_client)

    manual_converter = PDFConverterManual(storage_service, FILES_DIR)
    gotenberg_converter = PDFConverterGotenberg(storage_service, gotenberg_url="http://localhost:3000")

    context_data = {"name": "Gorro", "age": "Maakintosh", "description": "Consistency lorem ipsum"}

    # await manual_converter.generate_and_upload_pdf("manual_doc_1", context_data)
    # await gotenberg_converter.generate_and_upload_pdf("first_page.docx", "gotenberg_doc_1", context_data)
    # await gotenberg_converter.convert_pure_file('my-bucket', 'file.docx', 'documents', 'file.pdf')

    # file_beginning = await gotenberg_converter.generate_pdf_bytes("first_page.docx", context_data)
    #
    # file_end = await gotenberg_converter.generate_pdf_bytes("static.docx", None)
    #
    # full = await gotenberg_converter.merge_pdfs([file_beginning, file_end])
    #
    # await storage_service.upload_bytes('documents', 'full.pdf', full)

    await benchmark(storage_service, gotenberg_converter)


if __name__ == "__main__":
    asyncio.run(main())