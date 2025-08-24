from pathlib import Path
from io import BytesIO
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from playwright.async_api import async_playwright, Browser

class RenderService:
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"])
        )
        self.playwright = None
        self.browser: Browser | None = None

    async def start(self):
        """Levanta Playwright y un browser (Chromium)."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            args=["--allow-file-access-from-files"]
        )
        print("✅ Browser iniciado con soporte file://")

    async def stop(self):
        """Cierra browser y Playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🛑 Browser cerrado")

    async def render_to_png(self, template_name: str, params: dict) -> BytesIO:
        """
        Renderiza una plantilla Jinja2 a PNG en memoria.
        - Usa un tab nuevo por tarea concurrente.
        - Captura solo el div con id="content".
        """
        if not self.browser:
            await self.start()

        template_file = f"{template_name}.html.j2"
        try:
            template = self.env.get_template(template_file)
        except TemplateNotFound:
            raise ValueError(f"Template '{template_file}' no encontrado")

        html = template.render(**params)

        # Cada tarea crea su propia tab (aislamiento concurrente)
        page = await self.browser.new_page(viewport={"width": 1080, "height": 1920})
        try:
            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(1000)  # esperar CDN de Tailwind

            element = await page.query_selector("#content")
            if not element:
                raise ValueError("No se encontró div con id='content' en la plantilla")

            screenshot_bytes = await element.screenshot(type="png")
            return BytesIO(screenshot_bytes)
        finally:
            await page.close()
