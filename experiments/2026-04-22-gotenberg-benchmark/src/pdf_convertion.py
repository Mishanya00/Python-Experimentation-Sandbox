import uuid
import subprocess
import shutil
from io import BytesIO

import httpx
from docxtpl import DocxTemplate

from minio_service import MinioService
from minio_config import (
    minio_client,
    FILES_DIR,
)


async def generate_and_upload_pdf(filename: str, context: dict):
    storage = MinioService(minio_client)
    templates_bucket = 'pdf-generation'
    documents_bucket = 'documents'

    await storage.ensure_bucket_exists(documents_bucket)

    template_bytes = await storage.download_to_ram(templates_bucket, 'template1.docx')

    file_prefix = str(uuid.uuid4())[:8]

    docx_path = FILES_DIR / f"{filename}_{file_prefix}.docx"

    doc = DocxTemplate(template_bytes)
    doc.render(context)
    doc.save(docx_path)
    print(f"✅ Saved filled DOCX to {docx_path}")

    libreoffice_path = shutil.which('libreoffice')
    if not libreoffice_path:
        raise Exception("❌ LibreOffice not found on the system. Please install it.")

    subprocess.run([
        libreoffice_path,
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', str(FILES_DIR.resolve()),
        str(docx_path.resolve()),
    ],
        check=True,
        shell=False,
    )

    pdf_path = FILES_DIR / f"{docx_path.stem}.pdf"
    print(f"✅ Converted to PDF: {pdf_path}")

    final_object_name = f"{filename}.pdf"
    await storage.upload_file(
        bucket_name=documents_bucket,
        file_path=pdf_path,
        object_name=final_object_name
    )

    docx_path.unlink(missing_ok=True)
    pdf_path.unlink(missing_ok=True)

    return f"Done! File is in MinIO: {documents_bucket}/{final_object_name}"


async def generate_and_upload_pdf_gotenberg(filename: str, context: dict):
    storage = MinioService(minio_client)
    templates_bucket = 'pdf-generation'
    documents_bucket = 'documents'

    await storage.ensure_bucket_exists(documents_bucket)

    template_bytes = await storage.download_to_ram(templates_bucket, 'template1.docx')

    doc = DocxTemplate(template_bytes)
    doc.render(context)
    filled_docx_io = BytesIO()
    doc.save(filled_docx_io)
    filled_docx_io.seek(0)

    async with httpx.AsyncClient() as client:
        files = {
            'files': (f"{filename}.docx", filled_docx_io,
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }

        response = await client.post(
            'http://localhost:3000/forms/libreoffice/convert',
            files=files,
            timeout=120.0
        )
        response.raise_for_status()
        pdf_bytes = response.content

    final_object_name = f"{filename}.pdf"
    await storage.upload_bytes(
        bucket_name=documents_bucket,
        object_name=final_object_name,
        data=pdf_bytes
    )

    return f"Gotenberg Done! File is in MinIO: {documents_bucket}/{final_object_name}"


async def convert_pure_file_manual(source_bucket: str, source_object: str, dest_bucket: str, dest_object: str):
    """
    Downloads a file from MinIO to disk, uses local LibreOffice to convert it to PDF,
    uploads it back to MinIO, and cleans up disk.
    """
    storage = MinioService(minio_client)
    await storage.ensure_bucket_exists(dest_bucket)

    file_prefix = str(uuid.uuid4())[:8]

    temp_source_path = FILES_DIR / f"temp_source_{file_prefix}_{source_object}"

    await storage.download_file(source_bucket, source_object, temp_source_path)

    libreoffice_path = shutil.which('libreoffice')
    if not libreoffice_path:
        raise Exception("❌ LibreOffice not found on the system.")

    subprocess.run([
        libreoffice_path,
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', str(FILES_DIR.resolve()),
        str(temp_source_path.resolve()),
    ], check=True, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pdf_path = FILES_DIR / f"{temp_source_path.stem}.pdf"

    await storage.upload_file(
        bucket_name=dest_bucket,
        file_path=pdf_path,
        object_name=dest_object
    )

    temp_source_path.unlink(missing_ok=True)
    pdf_path.unlink(missing_ok=True)

    return f"Manual Pure Convert Done! {dest_bucket}/{dest_object}"


async def convert_pure_file_gotenberg(source_bucket: str, source_object: str, dest_bucket: str, dest_object: str):
    """
    Downloads a file from MinIO to RAM, streams it to Gotenberg to get PDF bytes,
    and uploads the bytes back to MinIO. (Zero disk IO)
    """
    storage = MinioService(minio_client)
    await storage.ensure_bucket_exists(dest_bucket)

    source_bytes_io = await storage.download_to_ram(source_bucket, source_object)

    async with httpx.AsyncClient() as client:
        files = {
            'files': (source_object, source_bytes_io, 'application/octet-stream')
        }

        response = await client.post(
            'http://localhost:3000/forms/libreoffice/convert',
            files=files,
            timeout=120.0
        )
        response.raise_for_status()
        pdf_bytes = response.content

    await storage.upload_bytes(
        bucket_name=dest_bucket,
        object_name=dest_object,
        data=pdf_bytes
    )

    return f"Gotenberg Pure Convert Done! {dest_bucket}/{dest_object}"