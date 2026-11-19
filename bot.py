import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
PUBLIC_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", "10000"))


async def ask_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            url,
            headers={"x-goog-api-key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salut ! Envoie /histoire suivi d'un genre.\n"
        "Exemples :\n/histoire horreur\n/histoire amour\n/histoire mystère"
    )


async def histoire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genre = " ".join(context.args) if context.args else "horreur"
    await update.message.reply_text("J'écris ton histoire, patiente un peu...")
    prompt = (
        f"Écris en français une histoire courte de type « {genre} » pour une vidéo "
        "TikTok de 45 à 60 secondes (environ 120 à 150 mots). "
        "Structure : une première phrase qui accroche tout de suite, un récit "
        "rythmé, une fin surprenante. Ensuite donne : "
        "1) un titre court et accrocheur, 2) une description d'une ligne, "
        "3) cinq hashtags. Histoire originale, sans contenu choquant ou violent gratuit."
    )
    try:
        texte = await ask_gemini(prompt)
        await update.message.reply_text(texte[:4000])
    except Exception as e:
        logging.exception("Erreur Gemini")
        await update.message.reply_text(f"Oups, erreur : {e}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("histoire", histoire))
    if PUBLIC_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{PUBLIC_URL}/{TOKEN}",
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    main()
