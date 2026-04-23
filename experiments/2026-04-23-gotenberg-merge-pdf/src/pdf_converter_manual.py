import uuid
import subprocess
import shutil
from pathlib import Path

from docxtpl import DocxTemplate
from minio_service import MinioService


class PDFConverterManual:
    def __init__(
            self,
            minio_service: MinioService,
            files_dir: Path,
            templates_bucket: str = 'pdf-generation',
            documents_bucket: str = 'documents',
    ):
        self._storage = minio_service
        self._files_dir = files_dir
        self._templates_bucket = templates_bucket
        self._documents_bucket = documents_bucket

    async def generate_and_upload_pdf(self, filename: str, context: dict) -> str:
        await self._storage.ensure_bucket_exists(self._documents_bucket)

        template_bytes = await self._storage.download_to_ram(self._templates_bucket, 'template1.docx')

        file_prefix = str(uuid.uuid4())[:8]
        docx_path = self._files_dir / f"{filename}_{file_prefix}.docx"

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
            '--outdir', str(self._files_dir.resolve()),
            str(docx_path.resolve()),
        ], check=True, shell=False)

        pdf_path = self._files_dir / f"{docx_path.stem}.pdf"
        print(f"✅ Converted to PDF: {pdf_path}")

        final_object_name = f"{filename}.pdf"
        await self._storage.upload_file(
            bucket_name=self._documents_bucket,
            file_path=pdf_path,
            object_name=final_object_name
        )

        docx_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)

        return f"Manual Render Done! File is in MinIO: {self._documents_bucket}/{final_object_name}"


    async def convert_pure_file(self, source_bucket: str, source_object: str, dest_bucket: str, dest_object: str) -> str:
        """
        Downloads a file from MinIO to disk, uses local LibreOffice to convert it to PDF,
        uploads it back to MinIO, and cleans up disk.
        """
        await self._storage.ensure_bucket_exists(dest_bucket)

        file_prefix = str(uuid.uuid4())[:8]
        temp_source_path = self._files_dir / f"temp_source_{file_prefix}_{source_object}"

        await self._storage.download_file(source_bucket, source_object, temp_source_path)

        libreoffice_path = shutil.which('libreoffice')
        if not libreoffice_path:
            raise Exception("❌ LibreOffice not found on the system.")

        subprocess.run([
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(self._files_dir.resolve()),
            str(temp_source_path.resolve()),
        ], check=True, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        pdf_path = self._files_dir / f"{temp_source_path.stem}.pdf"

        await self._storage.upload_file(
            bucket_name=dest_bucket,
            file_path=pdf_path,
            object_name=dest_object
        )

        temp_source_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)

        return f"Manual Pure Convert Done! {dest_bucket}/{dest_object}"