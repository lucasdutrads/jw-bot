import requests
from bs4 import BeautifulSoup
import time
import json
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.jw.org/pt/novidades/"
ARQUIVO = "enviados.json"

# =========================
# HISTÓRICO
# =========================
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r") as f:
        enviados = set(json.load(f))
else:
    enviados = set()

def salvar():
    with open(ARQUIVO, "w") as f:
        json.dump(list(enviados), f)

# =========================
# TELEGRAM
# =========================
def enviar_post(titulo, link, imagem, categoria, data):
    mensagem = (
        f"<b>{categoria} {titulo}</b>\n\n"
        f"📅 {data}\n\n"
        f"🔗 <a href=\"{link}\">Acessar conteúdo</a>"
    )
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "photo": imagem,
            "caption": mensagem,
            "parse_mode": "HTML"
        }
    )

def enviar_sem_imagem(titulo, link, categoria, data):
    mensagem = (
        f"<b>{categoria} {titulo}</b>\n\n"
        f"📅 {data}\n\n"
        f"🔗 {link}"
    )
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }
    )

def enviar_lista_novos(novos):
    for titulo, link, imagem, categoria, data in reversed(novos):
        if imagem:
            enviar_post(titulo, link, imagem, categoria, data)
        else:
            enviar_sem_imagem(titulo, link, categoria, data)
        time.sleep(2)

# =========================
# IDENTIFICAR CATEGORIA PELO LINK
# =========================
def identificar_tipo_pelo_link(link):
    if "/noticias/" in link:
        return "📰 Notícia"
    elif "/revistas/sentinela" in link:
        return "📖 A Sentinela"
    elif "/revistas/despertai" in link:
        return "📚 Despertai"
    elif "/videos/" in link:
        return "🎥 Vídeo"
    elif "/jw-apostila-do-mes/" in link:
        return "📘 Apostila"
    elif "/brochuras/" in link:
        return "📗 Brochura"
    elif "/musicas-canticos/" in link:
        return "🎵 Música"
    else:
        return "🔔 Atualização"

# =========================
# PEGAR NOVIDADES REAIS
# =========================
def pegar_novidades():
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Erro ao acessar site:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    novidades = []

    cards = soup.select("div.synopsis")

    for card in cards:
        link_tag = card.find_parent("a")
        if not link_tag:
            continue

        href = link_tag.get("href")
        if not href or not href.startswith("/pt/"):
            continue

        link = "https://www.jw.org" + href

        # 🔹 Remover apenas os links genéricos listados
        genericos = [
            "/pt/noticias/",
            "/pt/biblioteca/leituras-biblicas-dramatizadas/",
            "/pt/biblioteca/pecas-teatrais-biblicas/",
            "/pt/biblioteca/musicas-canticos/",
            "/pt/biblioteca/videos/",
            "/pt/biblioteca/videos/#pt/categories/VODStudio",
            "/pt/biblioteca/orientacoes/",
            "/pt/biblioteca/indices/"
        ]
        if any(h in link for h in genericos):
            continue

        titulo = card.get_text(strip=True)
        if len(titulo) < 10:
            continue

        img_tag = link_tag.find("img")
        imagem = "https://www.jw.org" + img_tag.get("src") if img_tag and img_tag.get("src") else None

        data_tag = card.find_next("div", class_="publicationDate")
        data = data_tag.get_text(strip=True) if data_tag else ""

        categoria = identificar_tipo_pelo_link(link)
        novidades.append((titulo, link, imagem, categoria, data))

    return novidades

# =========================
# VERIFICAR NOVOS POSTS
# =========================
def verificar():
    global enviados
    novidades = pegar_novidades()
    novos = []

    for titulo, link, imagem, categoria, data in novidades:
        if link not in enviados:
            enviados.add(link)
            novos.append((titulo, link, imagem, categoria, data))

    if novos:
        enviar_lista_novos(novos)
        salvar()

# =========================
# PRIMEIRA EXECUÇÃO
# =========================
if not os.path.exists(ARQUIVO):
    novidades = pegar_novidades()
    for _, link, _, _, _ in novidades:
        enviados.add(link)
    salvar()
    print("Inicializado sem enviar posts antigos")

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:
        verificar()
        time.sleep(300)
    except Exception as e:
        print("Erro no loop:", e)
        time.sleep(60)
