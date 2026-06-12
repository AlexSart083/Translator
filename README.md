# AI Translator – Streamlit

Versione web dell'AI Translator, eseguibile localmente o deployabile su [Streamlit Community Cloud](https://share.streamlit.io).

## Privacy & sicurezza

- Le API key **non vengono mai salvate sul server**.
- Vengono tenute solo nella sessione browser (in memoria).
- Puoi **scaricare** un `config.json` locale e **ricariarlo** la prossima volta: il file rimane sul tuo computer.
- Nessun database, nessun cloud storage proprietario.

---

## Setup rapido

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

> Python 3.10+ raccomandato.

### 2. Avvia l'app

```bash
streamlit run app.py
```

Il browser si apre automaticamente su `http://localhost:8501`.

### 3. Configura le API key

Nella barra laterale → **⚙ Impostazioni API** → incolla le chiavi → **Salva in sessione**.

Per riutilizzarle in futuro: **⬇ Scarica config.json**, poi nella prossima sessione **Carica config.json**.

---

## Ottenere le API key

| Provider    | URL                                          | Note                        |
|-------------|----------------------------------------------|-----------------------------|
| Gemini      | https://aistudio.google.com/apikey           | Piano gratuito disponibile  |
| OpenRouter  | https://openrouter.ai/keys                   | Molti modelli gratuiti      |

---

## Deploy su Streamlit Community Cloud

1. Carica questa cartella su GitHub (senza `config.json` — è locale!)
2. Vai su https://share.streamlit.io → "New app"
3. Punta al file `app.py`
4. Le API key si inseriscono dall'interfaccia, non servono secrets lato server

---

## Struttura del progetto

```
ai_translator_streamlit/
├── app.py               # App Streamlit principale
├── requirements.txt
├── core/
│   ├── __init__.py
│   └── translator.py    # Logica Gemini + OpenRouter (framework-agnostic)
└── README.md
```

---

## Funzionalità

- **Traduci** – 55+ lingue, rilevamento automatico
- **Riassumi** – riassunto conciso in lingua a scelta
- **Migliora** – chiarezza, grammatica, stile, leggibilità
- Selezione provider: Gemini o OpenRouter (con scelta del modello)
- Cronologia delle ultime 10 operazioni (in sessione)
- File `config.json` scaricabile/caricabile localmente
- Nessuna dipendenza esterna oltre a `streamlit`
