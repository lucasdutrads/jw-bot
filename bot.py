import requests
from bs4 import BeautifulSoup
import time
import json
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("TOKEN ou CHAT_ID não definidos!")

URL = "https://www.jw.org/pt/novidades/"
ARQUIVO = "enviados.json"

primeira_execucao = not os.path.exists(ARQUIVO)

# carregar histórico
if not primeira_execucao:
    with open(ARQUIVO, "r") as f:
        enviados = set(json.load(f))
else:
    enviados = set()

def salvar():
    with open(ARQUIVO, "w") as f:
        json.dump(list(enviados), f)

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

def identificar_tipo(titulo):
    t = titulo.lower()
    
    if "broadcasting" in t or "boletim" in t or "corpo governante" in t:
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
    global enviados, primeira_execucao
    
    try:
        r = requests.get(URL, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        
        artigos = soup.find_all("a", class_="teaserBlockLink") or []
        
        # 👇 LIMITA NA PRIMEIRA EXECUÇÃO
        if primeira_execucao:
            artigos = artigos[:10]

        novos = []
        
        for artigo in artigos:
            titulo = artigo.get_text(strip=True)
            link = "https://www.jw.org" + artigo.get("href")
            
            if link not in enviados:
                enviados.add(link)
                novos.append((titulo, link))
        
        if primeira_execucao:
            enviar_mensagem("📥 <b>Carregando últimos conteúdos do site...</b>")
        
        # envia do mais antigo pro mais novo
        for titulo, link in reversed(novos):
            emoji = identificar_tipo(titulo)
            mensagem = f"{emoji} <b>{titulo}</b>\n{link}"
            
            enviar_mensagem(mensagem)
            time.sleep(2)
        
        if novos:
            salvar()
            primeira_execucao = False

    except Exception as e:
        print("Erro ao verificar site:", e)

# mensagem inicial
enviar_mensagem("🤖 Bot iniciado e monitorando o jw.org...")

while True:
    verificar()
    time.sleep(300)
