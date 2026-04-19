"""
FORMA — Cucina, Macro, Fitness.
"""

import os

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
import anthropic

load_dotenv()

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ISTRUZIONI = """
Sei FORMA — un amico esperto di cucina, nutrizione e fitness. Parli in modo naturale, diretto, mai robotico.

Quando dai una ricetta:
- Inizia con il nome del piatto come titolo (##)
- Una riga con tempo e porzioni in corsivo
- Ingredienti come lista semplice
- Preparazione numerata, step chiari e umani (non telegrafici)
- Alla fine i macro in tabella: Kcal / Proteine / Carboidrati / Grassi
- Se utile aggiungi un consiglio pratico in fondo, max 2 righe

Per domande o consigli: rispondi come farebbe un amico che ne sa — diretto, caldo, senza elenchi inutili.

Niente emoji. Niente frasi di apertura tipo "certo!" o "ottima domanda". Vai subito al punto.
Italiano naturale. Numeri precisi dove servono.
"""

conversazione = []

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    global conversazione
    messaggio = request.json.get("messaggio", "")
    conversazione.append({"role": "user", "content": messaggio})

    profilo = request.json.get("profilo", "")
    sistema = ISTRUZIONI
    if profilo:
        sistema += f"\n\nPROFILO UTENTE (usa queste info per personalizzare ogni risposta):\n{profilo}"

    def genera():
        testo_completo = ""
        with claude.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=700,
            system=sistema,
            messages=conversazione
        ) as stream:
            for chunk in stream.text_stream:
                testo_completo += chunk
                yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
        conversazione.append({"role": "assistant", "content": testo_completo})
        if len(conversazione) > 20:
            conversazione[-20:]

    return Response(stream_with_context(genera()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/reset", methods=["POST"])
def reset():
    global conversazione
    conversazione = []
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
