from io import BytesIO

import httpx
from docxtpl import DocxTemplate
from minio_service import MinioService


class PDFConverterGotenberg:
    def __init__(
        self, 
        minio_service: MinioService, 
        gotenberg_url: str = "http://localhost:3000",
        templates_bucket: str = 'templates',
        documents_bucket: str = 'documents',
    ):
        self._storage = minio_service
        self._gotenberg_url = gotenberg_url
        self._templates_bucket = templates_bucket
        self._documents_bucket = documents_bucket

    async def _ensure_buckets_exist(self):
        await self._storage.ensure_bucket_exists(self._templates_bucket)
        await self._storage.ensure_bucket_exists(self._documents_bucket)

    async def generate_pdf_bytes(self, template: str, context: dict) -> bytes:
        await self._ensure_buckets_exist()

        template_bytes = await self._storage.download_to_ram(self._templates_bucket, template)

        doc = DocxTemplate(template_bytes)

        if context is not None:
            doc.render(context)

        filled_docx_io = BytesIO()
        doc.save(filled_docx_io)
        filled_docx_io.seek(0)

        async with httpx.AsyncClient() as client:
            files = {
                'files': (f"01.docx", filled_docx_io,
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }

            response = await client.post(
                f'{self._gotenberg_url}/forms/libreoffice/convert',
                files=files,
                timeout=120.0
            )
            response.raise_for_status()

            return response.content

    async def generate_and_upload_pdf(self, template: str, filename: str, context: dict) -> str:
        pdf_bytes = await self.generate_pdf_bytes(template, context)

        final_object_name = f"{filename}.pdf"
        await self._storage.upload_bytes(
            bucket_name=self._documents_bucket,
            object_name=final_object_name,
            data=pdf_bytes
        )

        return f"Gotenberg Render Done! File is in MinIO: {self._documents_bucket}/{final_object_name}"


    async def convert_pure_file(self, source_bucket: str, source_object: str, dest_bucket: str, dest_object: str) -> str:
        """
        Downloads a file from MinIO to RAM, streams it to Gotenberg to get PDF bytes,
        and uploads the bytes back to MinIO. (Zero disk IO)
        """
        await self._storage.ensure_bucket_exists(dest_bucket)

        source_bytes_io = await self._storage.download_to_ram(source_bucket, source_object)

        async with httpx.AsyncClient() as client:
            files = {
                'files': (source_object, source_bytes_io, 'application/octet-stream')
            }

            response = await client.post(
                f'{self._gotenberg_url}/forms/libreoffice/convert',
                files=files,
                timeout=120.0
            )
            response.raise_for_status()
            pdf_bytes = response.content

        await self._storage.upload_bytes(
            bucket_name=dest_bucket,
            object_name=dest_object,
            data=pdf_bytes
        )

        return f"Gotenberg Pure Convert Done! {dest_bucket}/{dest_object}"

    async def merge_pdfs(self, pdfs: list[bytes]) -> bytes:
        """
        Принимает список из PDF-байтов и склеивает их в один PDF через Gotenberg.
        Порядок в списке сохраняется.
        """
        if not pdfs:
            raise ValueError("❌ Empty PDF list provided for merging")

        if len(pdfs) == 1:
            return pdfs[0]

        files_payload = []
        for i, pdf_byte in enumerate(pdfs):
            # Gotenberg склеивает файлы строго по алфавиту имен файлов!
            # Называем их 000.pdf, 001.pdf, 002.pdf и т.д., чтобы гарантировать порядок.
            file_name = f"{i:03d}.pdf"

            # Формат httpx для отправки массива файлов с одинаковым ключом 'files':
            # ('имя_поля', ('имя_файла', контент, 'mime-type'))
            files_payload.append(
                ('files', (file_name, pdf_byte, 'application/pdf'))
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self._gotenberg_url}/forms/pdfengines/merge',
                files=files_payload,
                timeout=60.0
            )
            response.raise_for_status()

            return response.content