import io
import json
from flask_cors import CORS
import requests
from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os

from my_grocy import *

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)
app = Flask(__name__)
CORS(app)  # erlaubt alle Domains


main_prompt = ("You are an assistant managing the items in my household as well as the shoppinglist. "
               "Keep an eye on opened products and food which whill expire soon. use an informal tone but keep the answers short." 
               "The output is used for TTS. Don't add emojis. Keep the answers short. Always use the same language as in request.")


tools = [
    {
        "type": "function",
        "function": {
        "name": "get_amount_per_name",
        "description": "get the available amount of a product from grocy.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                }
            },
            "required": ["product_name"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "consumer_amount_per_name",
        "description": "eat, remove, consume or use a certain amount of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "Consumed amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "set_amount_per_name",
        "description": "set the total amount of a product in stock",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "new amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    },

    {
        "type": "function",
        "function": {
        "name": "add_amount_per_name",
        "description": "purchase or added a certain amount of a product to the stock",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of the Product"
                },
                "amount": {
                    "type": "string",
                    "description": "additional amount of the product"
                }
            },
            "required": ["product_name", "amount"]
        }
        }
    }
]

# Chatverläufe (pro Session-ID, z.B. "default")
chats = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_text = data.get("text")
    session = data.get("session", "default")

    if not user_text:
        return jsonify({"error": "Text fehlt"}), 400

    response = query_gpt(user_text)

    return response



def query_gpt(user_text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": main_prompt},
            {"role": "user", "content": user_text}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    print(message)

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_amount_per_name":
            result = get_amount_per_name(**arguments)
        elif function_name == "consumer_amount_per_name":
            result = consumer_amount_per_name(**arguments)
        elif function_name == "add_amount_per_name":
            result = add_amount_per_name(**arguments)
        elif function_name == "set_amount_per_name":
            result = set_amount_per_name(**arguments)
        else:
            # Falls keine Funktion notwendig
            return jsonify({"reply": message.content})

        followup = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": main_prompt},
                {"role": "user", "content": user_text},
                {
                    "role": "assistant",
                    "tool_calls": [tool_call.model_dump()]
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result)
                }
            ]
        )

        return jsonify({"reply": followup.choices[0].message.content})
    return jsonify({"reply": message.content})



def transcribe_with_whisper_server(filepath: str) -> str:
    url = "http://192.168.178.13:9025/asr"
    with open(filepath, "rb") as f:
        files = {"audio_file": ("input.wav", f, "audio/wav")}
        print("Sending files", f)
        response = requests.post(url, files=files)
        print(response.text)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception("Whisper-Serverfehler: " + response.text)


@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "Kein Text erhalten"}), 400
    api_key = os.getenv("ELEVEN_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID")  # z. B. "21m00Tcm4TlvDq8ikWAM"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return send_file(

        io.BytesIO(response.content),
        mimetype="audio/mpeg",
        as_attachment=False
    )


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "Keine Audiodatei erhalten"}), 400

    audio = request.files["audio"]
    path = os.path.join("uploads", "input.wav")
    audio.save(path)

    try:
        print("sending to whipser", path)
        user_text = transcribe_with_whisper_server(path)
        print("got from whipser", user_text)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    return query_gpt(user_text)



@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({"error": "Text fehlt"}), 400
    try:
        return query_gpt(user_text)
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
