import os
import json
import logging
import gradio as gr
from groq import Groq
import re

logging.basicConfig(level=logging.INFO)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "Eres Maya, una psicóloga clínica, terapeuta y consejera emocional. "
    "Tu ÚNICA Y EXCLUSIVA labor es escuchar activamente, brindar orientación psicológica, contención emocional y consejos humanos ante dificultades, ansiedad o problemas personales. "
    "REGLA ESTRICTA DE SEGURIDAD: TIENES TERMINANTEMENTE PROHIBIDO responder preguntas de programación, escribir código, corregir bugs de software, resolver tareas técnicas o matemáticas. "
    "Si alguien te pide código o temas ajenos al bienestar emocional, responde con amabilidad diciendo exactamente: "
    "'Mi propósito es exclusivamente brindarte apoyo emocional y orientación psicológica. No tengo permitido resolver dudas técnicas ni programar código. ¿Hay alguna situación personal o emocional en la que te pueda acompañar hoy?' "
    "NUNCA uses asteriscos, ni viñetas, ni markdown, ni emojis. Tus respuestas serán escuchadas por voz, así que redacta de forma cálida, cercana y en frases cortas de máximo dos a tres oraciones."
)

def clean_for_speech(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"[-_~]{2,}", "", text)
    text = re.sub(r"^\s*[-•*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*[-•]\s*", ", ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text

def respond_chat(user_message, history):
    if not user_message:
        return "", history
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.6,
            max_tokens=110
        )
        reply = clean_for_speech(completion.choices[0].message.content)
    except Exception as e:
        reply = "Lo siento, tuve un inconveniente de conexión. ¿Me puedes repetir lo que me decías?"

    history.append((user_message, reply))
    return reply, history

# Interfaz HTML interactiva moderna con voz nativa en el navegador
custom_html = """
<div style="text-align: center; padding: 20px; font-family: sans-serif;">
  <h2 style="color: #6366f1;">Maya AI - Tu Psicóloga y Consejera Emocional</h2>
  <p style="color: #64748b;">Habla por tu micrófono en español. Maya te escucha y te responde con voz en tiempo real.</p>
</div>
"""

with gr.Blocks(title="Maya AI - Psicóloga y Consejera") as demo:
    gr.HTML(custom_html)
    chatbot = gr.Chatbot(label="Sesión de Consejería", bubble_full_width=False)
    with gr.Row():
        msg_input = gr.Textbox(placeholder="Escribe o habla tu mensaje aquí...", scale=8, show_label=False)
        submit_btn = gr.Button("Enviar", variant="primary", scale=2)
    
    clear_btn = gr.Button("Reiniciar conversación", variant="secondary")

    def user_turn(msg, hist):
        return "", hist + [[msg, None]]

    def bot_turn(hist):
        user_msg = hist[-1][0]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in hist[:-1]:
            messages.append({"role": "user", "content": item[0]})
            if item[1]:
                messages.append({"role": "assistant", "content": item[1]})
        messages.append({"role": "user", "content": user_msg})

        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.6,
                max_tokens=110
            )
            reply = clean_for_speech(completion.choices[0].message.content)
        except Exception as e:
            reply = "Disculpa, hubo una dificultad procesando tu mensaje. ¿Cómo te sientes en este momento?"

        hist[-1][1] = reply
        return hist

    msg_input.submit(user_turn, [msg_input, chatbot], [msg_input, chatbot]).then(bot_turn, chatbot, chatbot)
    submit_btn.click(user_turn, [msg_input, chatbot], [msg_input, chatbot]).then(bot_turn, chatbot, chatbot)
    clear_btn.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
