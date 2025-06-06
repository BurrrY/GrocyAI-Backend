import io
from flask_cors import CORS
import requests
from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import logging
import graypy

from backend.tools import tools, function_map
from my_grocy import *

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)
app = Flask(__name__)
CORS(app)  # erlaubt alle Domains

# Create the logger
logger = logging.getLogger('the_logger')
logger.setLevel(logging.DEBUG)

os.makedirs("uploads", exist_ok=True)

main_prompt = os.environ.get("GROCY_AI_PROMPT", "You are an assistant managing the items in my household as well as the shoppinglist. "
               "Keep an eye on opened products and food which whill expire soon. use an informal tone but keep the answers short." 
               "The output is used for TTS. Don't add emojis. Keep the answers short. Always use the same language as in request.")


# Configure Graylog handler
# Replace with your Graylog server details
graylog_handler = graypy.GELFTCPHandler(os.environ.get("GRAYLOG_TCP_URL"), int(os.environ.get("GRAYLOG_TCP_PORT")))  # Use port 5514 instead of 514 if not running as root
logger.addHandler(graylog_handler)

# Also keep console logging if needed
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# Chatverläufe (pro Session-ID, z.B. "default")
chats = {}

@app.route("/chat", methods=["POST"])
def chat():
    logger.debug('chat upload endpoint accessed')
    data = request.get_json()
    user_text = data.get("text")
    logger.debug('chat message received',  extra={
        'user_text': user_text,
    })
    session = data.get("session", "default")

    if not user_text:
        return jsonify({"error": "Text fehlt"}), 400

    response = query_gpt(user_text)
    logger.debug('chat response',    extra={
        'response': response,
    })

    return response


def query_gpt(user_text: str) -> str:
    logger.debug('gpt-query',   extra={
        'user_text': user_text,
    })
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
    logger.debug('gpt-response',    extra={
        'response': message,
    })

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        logger.debug('gpt-tool-call function',  extra={
            'function_name': function_name,
        })

        if function_name in function_map:
            result = function_map[function_name](**arguments)
        else:

            logger.debug('gpt-tool-call no-function-response',  extra={
                'response': message.content,
            })
            return jsonify({"reply": message.content})

        logger.debug('gpt-tool-call function-response',  extra={
            'response': result,
        })
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

        logger.debug('gpt-tool-call gpt-response',  extra={
            'response': followup.choices[0].message.content,
        })
        return jsonify({"reply": followup.choices[0].message.content})


    logger.debug('gpt-tool message-response',  extra={
        'response': message.content,
    })
    return jsonify({"reply": message.content})



def transcribe_with_whisper_server(filepath: str) -> str:
    with open(filepath, "rb") as f:
        files = {"audio_file": ("input.wav", f, "audio/wav")}
        language = os.environ.get("WHISPER_LANGUAGE", "auto")
        base_url = os.environ.get("WHISPER_API_URL") + "/asr"
        url = f"{base_url}?language={language}"

        logger.debug('whisper-request', extra={
            'whisper_url': url,
            'language': language,
            'file': filepath
        })


        response = requests.post(url, files=files)

        print(response.text)
        if response.status_code == 200:
            logger.debug('whisper-response',  extra={
                'response': response.text,
            })
            return response.text
        else:
            logger.error('whisper-error-response',  extra={
                'response.text': response.text,
            })
            raise Exception("Whisper-Serverfehler: " + response.text)


@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text", "")
    logger.debug('tts-request',  extra={
        'request': text,
    })

    if not text:
        logger.error("No text in /tts")
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
        logger.debug("sending to whipser")
        user_text = transcribe_with_whisper_server(path)
        logger.debug("got from whipser", extra={
            'response': user_text,
        })

    except Exception as e:
        logger.error("Exception in upload-audio", extra={
            'Exception': e,
        })
        return jsonify({"error": str(e)}), 500


    return query_gpt(user_text)



@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_text = data.get("text", "")
    logger.debug("query-request", extra={
        'request': user_text,
    })

    if not user_text:
        logger.error("Kein user-text")
        return jsonify({"error": "Text fehlt"}), 400
    try:
        return query_gpt(user_text)
    except Exception as e:
        logger.error("Exception in query-request", extra={
            'Exception': e,
        })
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.debug("Starting app")
    logger.info("Connect to Grocy on URL: %s, Key: %s, Port: %s", os.environ.get("GROCY_API_URL"), os.environ.get("GROCY_API_KEY"), os.environ.get("GROCY_API_PORT"))
    app.run(host="0.0.0.0", port=5000)
