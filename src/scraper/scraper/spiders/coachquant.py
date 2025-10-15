import json
from urllib.parse import quote, urljoin, urlparse
import scrapy


class CoachQuantAllFirmsSpider(scrapy.Spider):
    name = "coachquant_all_firms"
    allowed_domains = ["coachquant.com", "www.coachquant.com"]
    start_urls = ["https://www.coachquant.com/questions"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 0.8,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9,es;q=0.8",
            "User-Agent": "Mozilla/5.0 (compatible; CQScraper/1.0; +https://example.com)",
        },
    }

    def parse(self, response):
        """
        Página índice /questions:
        - Detecta enlaces a las páginas de cada firma, típicamente '/jane-street', '/citadel', etc.
        """
        firms = set()
        for href in response.css("a::attr(href)").getall():
            if not href or not href.startswith("/"):
                continue
            # Nos quedamos con rutas de un solo segmento tipo '/jane-street' (no subrutas ni entrevistas)
            path = urlparse(href).path.strip("/")
            if not path or path == "questions" or "/" in path or "interview" in path:
                continue
            firms.add(urljoin(response.url, "/" + path))

        self.logger.info("Firmas detectadas: %d", len(firms))
        for firm_url in sorted(firms):
            yield scrapy.Request(firm_url, callback=self.parse_firm, cb_kwargs={"firm": firm_url.rsplit("/", 1)[-1]})

    def parse_firm(self, response, firm: str):
        """
        Página de una firma (p.ej., /jane-street):
        - Extrae todos los enlaces a preguntas dentro de esa firma (slug de 2+ segmentos).
        """
        question_links = set()
        base_path = f"/{firm}/"
        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            if href.startswith(base_path) and href.count("/") >= 2:
                # Filtra rutas irrelevantes
                if "/interview" in href or href.endswith(f"/{firm}"):
                    continue
                question_links.add(urljoin(response.url, href))

        self.logger.info("[%s] Preguntas detectadas: %d", firm, len(question_links))
        for q_url in sorted(question_links):
            yield scrapy.Request(q_url, callback=self.parse_question_page, cb_kwargs={"firm": firm})

    def parse_question_page(self, response, firm: str):
        """
        Página de una pregunta:
        - Lee el <h1> para obtener el TÍTULO exacto.
        - Construye la URL del JSON oficial: /questions/<TÍTULO>.json (URL-encoded).
        """
        title = response.css("main h1::text").get(default="").strip()
        if not title:
            self.logger.warning("[%s] No encontré título en %s", firm, response.url)
            return

        json_url = f"https://www.coachquant.com/questions/{quote(title)}.json"
        meta = {
            "firm": firm,
            "title": title,
            "url_page": response.url,
        }
        yield scrapy.Request(json_url, callback=self.parse_question_json, meta=meta, errback=self.on_json_error)

    def parse_question_json(self, response):
        """
        JSON oficial de la pregunta: normalmente incluye difficulty, tags, question, answer (y a veces *_html).
        """
        data = json.loads(response.text)

        difficulty = data.get("difficulty")
        tags = data.get("tags") or data.get("topics")
        question_text = data.get("question") or data.get("prompt") or data.get("body")
        answer_text = data.get("answer") or data.get("solution")
        answer_html = data.get("answer_html") or data.get("solution_html")

        yield {
            "firm": response.meta["firm"],
            "title": response.meta["title"],
            "url_page": response.meta["url_page"],
            "url_json": response.url,
            "difficulty": difficulty,
            "tags": tags,
            "question_text": question_text,
            "answer_text": answer_text,
            "answer_html": answer_html,  # conserva fórmulas si vienen en HTML/MathML
            "raw": data,                 # útil por si cambia el esquema
        }

    def on_json_error(self, failure):
        """
        Si el JSON devuelve error (404, etc.), lo registramos con contexto.
        """
        request = failure.request
        firm = request.meta.get("firm")
        title = request.meta.get("title")
        url_page = request.meta.get("url_page")
        self.logger.error("Fallo JSON [%s] '%s': %s (desde %s)", firm, title, request.url, url_page)
