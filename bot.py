import requests
from bs4 import BeautifulSoup
import time
import json
import os

# 📤 Webhook de Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1398261761005846578/RyMCKBwQ56vb3g7xTsOmjIP5lYp77NDU5IPSMeOB9kCGGOCah-ss_5DZMXiFX1Yo962T"

# ⏱️ Tiempo de espera entre ejecuciones (en segundos)
WAIT_TIME_SECONDS = 3600  # 1 hora

# 🔎 Palabras clave mejoradas
KEYWORDS = [
    "EIR", "EIR 2025", "EIR 2026", "enfermería", "enfermeria", "plazas EIR",
    "academia EIR", "IFSES EIR", "matrícula EIR", "EIR inscripción", "calendario EIR", "Formación Sanitaria Especializada",
    "oferta plazas sanidad"
]

# 🌐 Páginas HTML para revisar
HTML_SOURCES = [
    "https://www.redaccionmedica.com/secciones/eir-y-mas-residentes",
    "https://www.noticiasensalud.com/",
    "https://www.sanidad.gob.es/gabinete/notasPrensa.do",
    "https://ifses.es/noticias-ifses/",
    "https://diarioenfermero.es/"
]

# 📁 Archivo para guardar los enlaces notificados
NOTIFIED_FILE = "notified_links.json"
notified_links = set()


def cargar_notificados():
    if os.path.exists(NOTIFIED_FILE):
        try:
            with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Error al cargar archivo de notificados: {e}")
    return set()


def guardar_notificados():
    try:
        with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(notified_links), f, indent=2)
    except Exception as e:
        print(f"❌ Error al guardar archivo de notificados: {e}")


def contiene_keywords(texto):
    texto = texto.lower()
    for kw in KEYWORDS:
        palabras = kw.lower().split()
        if all(palabra in texto for palabra in palabras):
            return True
    return False


def obtener_imagen(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for prop in ["og:image", "twitter:image"]:
            meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if meta and meta.get("content"):
                return meta["content"]
    except Exception as e:
        print(f"⚠️ No se pudo obtener imagen de {url}: {e}")
    return None


def enviar_a_discord(title, link):
    imagen = obtener_imagen(link)

    embed = {
        "title": title,
        "url": link,
        "color": 0x3498db,
        "footer": {"text": "Bot EIR"},
    }

    if imagen:
        embed["image"] = {"url": imagen}

    data = {
        "embeds": [embed]
    }

    try:
        print(f"📤 Enviando embed: {title}")
        requests.post(DISCORD_WEBHOOK_URL, json=data)
        notified_links.add(link)
        guardar_notificados()
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")


def scrape_html(url):
    print(f"🔎 Revisando: {url}")
    noticias = []

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        enlaces = soup.find_all("a", href=True)

        for enlace in enlaces:
            if len(noticias) >= 5:
                break

            titulo = enlace.get_text(strip=True)
            href = enlace["href"]
            if not titulo or len(titulo) < 10:
                continue
            if not href.startswith("http"):
                href = requests.compat.urljoin(url, href)
            if href in notified_links:
                print(f"⛔ Ya se notificó: {href}. Deteniendo búsqueda en esta URL.")
                break
            if contiene_keywords(titulo):
                noticias.append({
                    "title": titulo,
                    "link": href,
                })
    except Exception as e:
        print(f"⚠️ Error al scrapear {url}: {e}")

    return noticias


def main():
    global notified_links
    notified_links = cargar_notificados()

    while True:
        for url in HTML_SOURCES:
            noticias = scrape_html(url)
            for noticia in noticias:
                if noticia["link"] not in notified_links:
                    enviar_a_discord(noticia["title"], noticia["link"])
        print(f"⏳ Esperando {WAIT_TIME_SECONDS / 60:.0f} minutos...\n")
        time.sleep(WAIT_TIME_SECONDS)


if __name__ == "__main__":
    main()
