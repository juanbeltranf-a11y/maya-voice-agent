import os
import json
import logging
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("webrtc_voice_agent")

app = FastAPI(title="WebRTC Voice Agent - Groq LPU")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

import re

def clean_for_speech(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"[-_~]{2,}", "", text)
    text = re.sub(r"^\s*[-•*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*[-•]\s*", ", ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text

SYSTEM_PROMPT = (
    "Eres Maya, una psicóloga clínica, terapeuta y consejera emocional. "
    "Tu ÚNICA Y EXCLUSIVA labor es escuchar, brindar orientación psicológica, contención emocional y consejos humanos ante situaciones de vida, estrés, ansiedad o problemas personales. "
    "REGLA DE SEGURIDAD ESTRICTA: TIENES TERMINANTEMENTE PROHIBIDO responder dudas de programación, escribir código, corregir bugs de software, hablar de desarrollo web o resolver tareas técnicas. "
    "Si alguien te pide código, ayuda técnica o cualquier tema ajeno a la salud mental, rechaza cortés y firmemente diciendo: "
    "'Mi propósito es exclusivamente brindarte apoyo emocional y orientación psicológica. No tengo permitido resolver dudas técnicas ni programar código. ¿Hay alguna situación personal o emocional en la que te pueda acompañar hoy?' "
    "NUNCA uses asteriscos, viñetas, markdown ni emojis. Tus respuestas serán escuchadas por voz, así que habla con naturalidad, cercanía y calidez humana."
)

@app.get("/")
def read_root():
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Maya AI - Agente de Voz Web (Groq LPU)</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --card: rgba(18, 22, 34, 0.7);
      --accent: #6366f1;
      --accent-glow: rgba(99, 102, 241, 0.4);
      --text: #f8fafc;
      --subtext: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body {
      background: radial-gradient(circle at 50% 20%, #151a30 0%, #07090e 80%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      overflow-x: hidden;
    }
    .container {
      max-width: 520px;
      width: 100%;
      background: var(--card);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 28px;
      padding: 36px 28px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.6), 0 0 40px var(--accent-glow);
      text-align: center;
      position: relative;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 700;
      color: #a5b4fc;
      letter-spacing: 0.5px;
      margin-bottom: 20px;
    }
    .badge .dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } }
    h1 { font-size: 2.1rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }
    p.subtitle { color: var(--subtext); font-size: 0.95rem; margin-bottom: 30px; }

    /* Visualizer Orb */
    .orb-container {
      position: relative;
      width: 170px;
      height: 170px;
      margin: 0 auto 32px auto;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .orb {
      width: 120px;
      height: 120px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
      box-shadow: 0 0 50px rgba(168, 85, 247, 0.5);
      cursor: pointer;
      transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      outline: none;
      z-index: 2;
    }
    .orb:hover { transform: scale(1.08); box-shadow: 0 0 70px rgba(168, 85, 247, 0.8); }
    .orb svg { width: 44px; height: 44px; fill: white; transition: 0.3s; }
    
    .wave-ring {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      border: 2px solid rgba(168, 85, 247, 0.3);
      opacity: 0;
      pointer-events: none;
    }
    .listening .orb {
      animation: beat 1s infinite alternate;
      background: linear-gradient(135deg, #ef4444, #f59e0b);
      box-shadow: 0 0 60px rgba(239, 68, 68, 0.7);
    }
    .listening .wave-ring {
      animation: ripple 1.6s infinite cubic-bezier(0, 0.2, 0.8, 1);
    }
    .speaking .orb {
      animation: beat 0.6s infinite alternate;
      background: linear-gradient(135deg, #10b981, #06b6d4);
      box-shadow: 0 0 60px rgba(16, 185, 129, 0.7);
    }
    @keyframes beat { 0% { transform: scale(0.96); } 100% { transform: scale(1.1); } }
    @keyframes ripple {
      0% { transform: scale(0.8); opacity: 0.8; }
      100% { transform: scale(1.6); opacity: 0; }
    }

    .status-text {
      font-size: 1rem;
      font-weight: 600;
      color: #cbd5e1;
      margin-bottom: 24px;
      min-height: 24px;
    }
    .chat-box {
      background: rgba(10, 14, 23, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 18px;
      padding: 16px;
      max-height: 180px;
      overflow-y: auto;
      text-align: left;
      font-size: 0.9rem;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .msg { padding: 8px 12px; border-radius: 12px; max-width: 85%; }
    .msg.user { background: rgba(99, 102, 241, 0.25); align-self: flex-end; color: #e0e7ff; }
    .msg.ai { background: rgba(255, 255, 255, 0.06); align-self: flex-start; color: #f1f5f9; }
    
    .footer-note {
      margin-top: 22px;
      font-size: 0.75rem;
      color: #64748b;
    }
  </style>
</head>
<body>

  <div class="container">
    <div class="badge">
      <span class="dot"></span>
      GROQ LPU • WEBRTC CALL
    </div>

    <h1>Habla con Maya</h1>
    <p class="subtitle">Llamada de voz en tiempo real sin costo telefónico</p>

    <div class="orb-container" id="orbContainer">
      <div class="wave-ring"></div>
      <button class="orb" id="micBtn" onclick="toggleCall()">
        <svg id="micIcon" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      </button>
    </div>

    <div class="status-text" id="statusLabel">Toca el orbe para iniciar la llamada</div>

    <div class="chat-box" id="chatBox">
      <div class="msg ai"><b>Maya:</b> ¡Hola Juan! Presiona el botón para hablar conmigo por tu micrófono. Te responderé al instante.</div>
    </div>

    <div class="footer-note">
      Ultra-baja latencia • Speech-to-Speech nativo con Groq • Totalmente gratis
    </div>
  </div>

  <script>
    let isCalling = false;
    let recognition;
    let synth = window.speechSynthesis;
    let chatHistory = [];
    let silenceTimer = null;
    let accumulatedTranscript = "";
    let isSpeaking = false;

    const orbContainer = document.getElementById('orbContainer');
    const statusLabel = document.getElementById('statusLabel');
    const chatBox = document.getElementById('chatBox');

    // Inicializar Web Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = 'es-CO'; // Español natural
      recognition.continuous = true; // No cortar ante pausas cortas
      recognition.interimResults = true; // Mostrar mientras hablas

      recognition.onstart = () => {
        orbContainer.className = 'orb-container listening';
        statusLabel.innerText = 'Escuchando... Puedes hablar con pausas naturales';
      };

      recognition.onresult = (event) => {
        if (isSpeaking) return; // Ignorar por completo si Maya está hablando
        let interimText = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            accumulatedTranscript += ' ' + event.results[i][0].transcript;
          } else {
            interimText += event.results[i][0].transcript;
          }
        }

        const currentText = (accumulatedTranscript + ' ' + interimText).trim();
        if (currentText) {
          statusLabel.innerText = `"${currentText.slice(-45)}..."`;
          
          // Reiniciar temporizador de silencio: espera 2.2 segundos de silencio real antes de enviar a Groq
          clearTimeout(silenceTimer);
          silenceTimer = setTimeout(async () => {
            const finalQuery = accumulatedTranscript.trim() || interimText.trim();
            if (finalQuery.length > 2) {
              accumulatedTranscript = "";
              recognition.stop();
              addMessage('user', finalQuery);
              statusLabel.innerText = 'Pensando con Groq LPU...';
              orbContainer.className = 'orb-container';
              await sendToGroq(finalQuery);
            }
          }, 2200);
        }
      };

      recognition.onerror = (e) => {
        console.warn('Recognition notice:', e.error);
        if (e.error !== 'no-speech') {
          orbContainer.className = 'orb-container';
        }
      };

      recognition.onend = () => {
        if (isCalling && !isSpeaking) {
          // Si sigue la llamada y no está hablando Maya, reiniciar escucha continua
          setTimeout(() => {
            try { recognition.start(); } catch(err){}
          }, 300);
        }
      };
    } else {
      statusLabel.innerText = 'Tu navegador no soporta reconocimiento de voz nativo. Usa Chrome o Edge.';
    }

    function toggleCall() {
      if (!recognition) return;
      if (!isCalling) {
        isCalling = true;
        accumulatedTranscript = "";
        statusLabel.innerText = 'Conectando llamada...';
        startListening();
      } else {
        // Detener o reiniciar
        if (synth.speaking) {
          synth.cancel();
          isSpeaking = false;
        }
        accumulatedTranscript = "";
        clearTimeout(silenceTimer);
        startListening();
      }
    }

    function startListening() {
      try {
        recognition.start();
      } catch (e) {
        recognition.stop();
        setTimeout(() => {
          try { recognition.start(); } catch(err){}
        }, 200);
      }
    }

    async function sendToGroq(userText) {
      try {
        chatHistory.push({ role: 'user', content: userText });
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: chatHistory })
        });
        const data = await res.json();
        const reply = data.reply;
        chatHistory.push({ role: 'assistant', content: reply });
        addMessage('ai', reply);
        speakReply(reply);
      } catch (err) {
        console.error(err);
        statusLabel.innerText = 'Error de conexión con Groq.';
        isCalling = false;
      }
    }

    function speakReply(text) {
      if (!synth) return;
      synth.cancel();
      isSpeaking = true;

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-MX';
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      const voices = synth.getVoices();
      const spanishVoice = voices.find(v => v.lang.startsWith('es') && (v.name.includes('Natural') || v.name.includes('Neural') || v.name.includes('Google') || v.name.includes('Paulina') || v.name.includes('Monica') || v.name.includes('Helena')));
      if (spanishVoice) utterance.voice = spanishVoice;

      utterance.onstart = () => {
        isSpeaking = true;
        try { recognition.abort(); } catch(e) {} // Detener microfono para que NO capture su propia voz
        orbContainer.className = 'orb-container speaking';
        statusLabel.innerText = 'Maya está hablando...';
      };

      utterance.onend = () => {
        isSpeaking = false;
        accumulatedTranscript = "";
        clearTimeout(silenceTimer);
        orbContainer.className = 'orb-container listening';
        statusLabel.innerText = 'Te escucho... habla cuando gustes';
        // Esperar 400ms tras terminar el audio para reactivar el microfono limpio
        setTimeout(() => {
          if (isCalling && !isSpeaking) {
            startListening();
          }
        }, 400);
      };

      synth.speak(utterance);
    }

    function addMessage(sender, text) {
      const msg = document.createElement('div');
      msg.className = `msg ${sender}`;
      msg.innerHTML = `<b>${sender === 'user' ? 'Tú' : 'Maya'}:</b> ${text}`;
      chatBox.appendChild(msg);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = () => synth.getVoices();
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

@app.post("/api/chat")
async def chat_with_groq(payload: dict):
    user_messages = payload.get("messages", [])
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=full_messages,
            temperature=0.6,
            max_tokens=100
        )
        reply = clean_for_speech(completion.choices[0].message.content)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Error en Groq: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
