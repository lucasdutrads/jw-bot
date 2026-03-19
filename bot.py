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
    """
    Envia todos os novos posts em sequência, respeitando imagem e texto.
    """
    for titulo, link, imagem, data in reversed(novos):
        categoria = identificar_tipo(titulo)
        if imagem:
            enviar_post(titulo, link, imagem, categoria, data)
        else:
            enviar_sem_imagem(titulo, link, categoria, data)
        time.sleep(2)  # pequeno intervalo entre envios

# =========================
# IDENTIFICAR TIPO
# =========================
def identificar_tipo(titulo):
    t = titulo.lower()
    if "broadcasting" in t or "boletim" in t:
        return "🎥 Vídeo"
    elif "sentinela" in t:
        return "📖 A Sentinela"
    elif "despertai" in t:
        return "📚 Despertai"
    elif "notícia" in t:
        return "📰 Notícia"
    else:
        return "🔔 Atualização"

# =========================
# PEGAR NOVIDADES
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

        titulo = card.get_text(strip=True)
        if len(titulo) < 10:
            continue

        img_tag = link_tag.find("img")
        if img_tag and img_tag.get("src"):
            imagem = "https://www.jw.org" + img_tag.get("src")
        else:
            imagem = None

        data_tag = card.find_next("div", class_="publicationDate")
        data = data_tag.get_text(strip=True) if data_tag else ""

        novidades.append((titulo, link, imagem, data))

    return novidades

# =========================
# VERIFICAR NOVOS POSTS
# =========================
def verificar():
    global enviados
    novidades = pegar_novidades()
    novos = []

    for titulo, link, imagem, data in novidades:
        if link not in enviados:
            enviados.add(link)
            novos.append((titulo, link, imagem, data))

    if novos:
        enviar_lista_novos(novos)
        salvar()

# =========================
# PRIMEIRA EXECUÇÃO
# =========================
if not os.path.exists(ARQUIVO):
    novidades = pegar_novidades()
    for _, link, _, _ in novidades:
        enviados.add(link)
    salvar()
    print("Inicializado sem enviar posts antigos")

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:
        verificar()
        time.sleep(300)  # 5 minutos
    except Exception as e:
        print("Erro no loop:", e)
        time.sleep(60)
