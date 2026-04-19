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

@app.route("/foto", methods=["POST"])
def analizza_foto():
    data = request.json
    img_b64 = data.get("immagine", "")
    media_type = data.get("tipo", "image/jpeg")
    if not img_b64:
        return jsonify({"ok": False, "errore": "nessuna immagine"}), 400
    try:
        risposta = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": img_b64}
                    },
                    {
                        "type": "text",
                        "text": 'Sei un nutrizionista preciso. Analizza il pasto in questa foto e stima i macro per la porzione visibile. Rispondi SOLO con JSON valido, zero testo extra: {"nome":"nome del piatto","kcal":0,"prot":0,"carb":0,"grassi":0,"note":"breve nota sulla stima (es. porzione media, difficile stimare la salsa)"}'
                    }
                ]
            }]
        )
        testo = risposta.content[0].text.strip()
        # Estrai JSON anche se Claude aggiunge testo attorno
        import re, json
        match = re.search(r'\{.*\}', testo, re.DOTALL)
        if match:
            risultato = json.loads(match.group())
            return jsonify({"ok": True, "risultato": risultato})
        return jsonify({"ok": False, "errore": "risposta non parsabile", "raw": testo})
    except Exception as e:
        return jsonify({"ok": False, "errore": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset():
    global conversazione
    conversazione = []
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
