import asyncio
from io import BytesIO
from pathlib import Path

import httpx
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage


class GotenbergImageDocGenerator:
    """
    Standalone helper to render a DOCX template that contains image placeholders
    ({{ logo }}, {{ qr_code }}) and convert it to PDF via Gotenberg.

    Intended for testing Gotenberg's image capabilities before wiring into prod.
    """

    def __init__(
        self,
        gotenberg_url: str = "http://localhost:3000",
        timeout: float = 120.0,
    ):
        self.gotenberg_url = gotenberg_url.rstrip("/")
        self.timeout = timeout

    # ---------- public API ----------

    async def generate_pdf_bytes(
        self,
        template_path: str | Path,
        context: dict,
        logo_path: str | Path,
        qr_path: str | Path,
        *,
        logo_width_mm: float = 40,
        qr_width_mm: float = 30,
    ) -> bytes:
        """
        Render DOCX (with images injected) and return the resulting PDF bytes.
        """
        filled_docx = self._render_docx_with_images(
            template_path=template_path,
            context=context,
            logo_path=logo_path,
            qr_path=qr_path,
            logo_width_mm=logo_width_mm,
            qr_width_mm=qr_width_mm,
        )
        return await self._convert_to_pdf_via_gotenberg(
            filename=Path(template_path).stem,
            docx_bytes=filled_docx,
        )

    async def generate_pdf_file(
        self,
        template_path: str | Path,
        context: dict,
        logo_path: str | Path,
        qr_path: str | Path,
        output_path: str | Path,
        *,
        logo_width_mm: float = 40,
        qr_width_mm: float = 30,
    ) -> Path:
        """
        Same as generate_pdf_bytes but writes result to disk for easy inspection.
        """
        pdf_bytes = await self.generate_pdf_bytes(
            template_path=template_path,
            context=context,
            logo_path=logo_path,
            qr_path=qr_path,
            logo_width_mm=logo_width_mm,
            qr_width_mm=qr_width_mm,
        )
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)
        return output_path

    # ---------- internals ----------

    def _render_docx_with_images(
        self,
        template_path: str | Path,
        context: dict,
        logo_path: str | Path,
        qr_path: str | Path,
        logo_width_mm: float,
        qr_width_mm: float,
    ) -> bytes:
        template_path = Path(template_path)
        logo_path = Path(logo_path)
        qr_path = Path(qr_path)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        if not logo_path.exists():
            raise FileNotFoundError(f"Logo not found: {logo_path}")
        if not qr_path.exists():
            raise FileNotFoundError(f"QR not found: {qr_path}")

        doc = DocxTemplate(str(template_path))

        # InlineImage needs an open binary stream; keep them alive until doc.save()
        logo_stream = logo_path.open("rb")
        qr_stream = qr_path.open("rb")

        try:
            # `context` from caller is copied so we don't mutate it
            render_ctx = dict(context)
            render_ctx["logo"] = InlineImage(doc, logo_stream, width=Mm(logo_width_mm))
            render_ctx["qr_code"] = InlineImage(doc, qr_stream, width=Mm(qr_width_mm))

            doc.render(render_ctx)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        finally:
            logo_stream.close()
            qr_stream.close()

    async def _convert_to_pdf_via_gotenberg(
        self,
        filename: str,
        docx_bytes: bytes,
    ) -> bytes:
        url = f"{self.gotenberg_url}/forms/libreoffice/convert"

        files = {
            "files": (
                f"{filename}.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, files=files, timeout=self.timeout)
            response.raise_for_status()
            return response.content


# ---------------------------------------------------------------------------
# Manual test entrypoint — run with:  python gotenberg_test.py
# ---------------------------------------------------------------------------
async def _main():
    base_dir = Path(__file__).parent / "files"

    generator = GotenbergImageDocGenerator(
        gotenberg_url="http://localhost:3000",
    )

    # Put whatever text/placeholders your template expects here.
    # (Only `logo` and `qr_code` are handled automatically by the class.)
    context = {
        "money": "12345.67",
        "currency": "BYN",
    }

    output_path = await generator.generate_pdf_file(
        template_path=base_dir / "libre_template.docx",
        context=context,
        logo_path=base_dir / "logo.png",
        qr_path=base_dir / "qr.png",
        output_path=Path(__file__).parent / "out" / "gotenberg_image_test.pdf",
        logo_width_mm=40,
        qr_width_mm=30,
    )

    print(f"✅ PDF written to: {output_path}")


if __name__ == "__main__":
    asyncio.run(_main())