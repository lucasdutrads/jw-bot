import requests
from bs4 import BeautifulSoup
import time
import json
import os

TOKEN = "8650008100:AAElTKfTT4ghB2Q32nEqlW9_iPVAQ1kdmtY"
CHAT_ID = "977648602"

URL = "https://www.jw.org/pt/novidades/"
ARQUIVO = "enviados.json"

# carregar histórico
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r") as f:
        enviados = set(json.load(f))
else:
    enviados = set()

def salvar():
    with open(ARQUIVO, "w") as f:
        json.dump(list(enviados), f)

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

def identificar_tipo(titulo):
    t = titulo.lower()
    
    if "broadcasting" in t or "boletim" in t:
        return "🎥"
    elif "watchtower" in t or "sentinela" in t:
        return "📖"
    elif "despertai" in t:
        return "📚"
    elif "notícia" in t or "news" in t:
        return "📰"
    else:
        return "🔔"

def verificar():
    global enviados
    
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    
    artigos = soup.find_all("a", class_="teaserBlockLink")
    
    novos = []
    
    for artigo in artigos:
        titulo = artigo.get_text(strip=True)
        link = "https://www.jw.org" + artigo.get("href")
        
        if link not in enviados:
            enviados.add(link)
            novos.append((titulo, link))
    
    # envia do mais antigo pro mais novo
    for titulo, link in reversed(novos):
        emoji = identificar_tipo(titulo)
        
        mensagem = f"{emoji} <b>{titulo}</b>\n{link}"
        enviar_mensagem(mensagem)
        time.sleep(2)  # evita flood
    
    if novos:
        salvar()

# mensagem inicial
enviar_mensagem("🤖 Bot iniciado e monitorando o jw.org...")

while True:
    try:
        verificar()
        time.sleep(300)  # 5 minutos
    except Exception as e:
        print("Erro:", e)
        time.sleep(60)