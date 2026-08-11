import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import tensorflow as tf

from flask import Flask, render_template, request, jsonify
from PIL import Image
from dotenv import load_dotenv

from google import genai
from google.genai import types
from supabase import create_client


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# 2. CHECK ENVIRONMENT VARIABLES
# ============================================================

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing from .env")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing from .env")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")


# ============================================================
# 3. CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# 4. CONNECT TO SUPABASE
# ============================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# 5. CONNECT TO GEMINI
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# 6. LOAD TRAINED DISEASE MODEL
# ============================================================

print("Loading disease model...")

model = tf.keras.models.load_model(
    "disease_model.keras"
)

with open("class_names.txt", "r") as file:

    class_names = [
        line.strip()
        for line in file.readlines()
    ]

print("Disease model loaded successfully.")
print("Number of classes:", len(class_names))


# ============================================================
# 7. HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# 8. DISEASE PREDICTION
# ============================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        if "image" not in request.files:

            return jsonify({
                "success": False,
                "message": "No image uploaded."
            })

        file = request.files["image"]

        if file.filename == "":

            return jsonify({
                "success": False,
                "message": "No image selected."
            })


        # ----------------------------------------------------
        # OPEN IMAGE
        # ----------------------------------------------------

        image = Image.open(
            file
        ).convert("RGB")


        # ----------------------------------------------------
        # RESIZE IMAGE
        # ----------------------------------------------------

        image = image.resize(
            (224, 224)
        )


        # ----------------------------------------------------
        # CONVERT TO NUMPY
        # ----------------------------------------------------

        image_array = np.array(
            image
        )

        image_array = (
            image_array / 255.0
        )

        image_array = np.expand_dims(
            image_array,
            axis=0
        )


        # ----------------------------------------------------
        # PREDICT
        # ----------------------------------------------------

        predictions = model.predict(
            image_array,
            verbose=0
        )


        predicted_index = np.argmax(
            predictions[0]
        )

        predicted_class = class_names[
            predicted_index
        ]

        confidence = (
            float(
                predictions[0][
                    predicted_index
                ]
            ) * 100
        )


        return jsonify({

            "success": True,

            "disease": predicted_class,

            "confidence": round(
                confidence,
                2
            )

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        })


# ============================================================
# 9. CREATE GEMINI EMBEDDING
# ============================================================

def create_embedding(text):

    response = client.models.embed_content(

        model="gemini-embedding-001",

        contents=text,

        config=types.EmbedContentConfig(
            output_dimensionality=768
        )

    )

    return response.embeddings[
        0
    ].values


# ============================================================
# 10. RETRIEVE KNOWLEDGE FROM SUPABASE
# ============================================================

def retrieve_documents(
    query_embedding
):

    result = supabase.rpc(

        "match_documents",

        {

            "query_embedding":
                query_embedding,

            "match_threshold":
                0.0,

            "match_count":
                5

        }

    ).execute()


    return result.data


# ============================================================
# 11. DISEASE QUESTION + RAG
# ============================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    try:

        data = request.get_json()

        question = data.get(
            "question",
            ""
        )

        disease = data.get(
            "disease",
            ""
        )


        if not question:

            return jsonify({

                "success": False,

                "message":
                    "Please enter a question."

            })


        # ----------------------------------------------------
        # CREATE SEARCH QUERY
        # ----------------------------------------------------

        query = f"""
Disease: {disease}

User Question:
{question}
"""


        # ----------------------------------------------------
        # CREATE EMBEDDING
        # ----------------------------------------------------

        embedding = create_embedding(
            query
        )


        # ----------------------------------------------------
        # SEARCH SUPABASE
        # ----------------------------------------------------

        documents = retrieve_documents(
            embedding
        )


        # ----------------------------------------------------
        # CREATE CONTEXT
        # ----------------------------------------------------

        context = ""

        for i, document in enumerate(
            documents
        ):

            content = document.get(
                "content",
                ""
            )

            context += (
                f"\nDocument {i + 1}:\n"
                f"{content}\n"
            )


        # ----------------------------------------------------
        # GEMINI PROMPT
        # ----------------------------------------------------

        prompt = f"""

You are an agriculture AI assistant.

Predicted Disease:
{disease}

User Question:
{question}

Retrieved Agricultural Knowledge:
{context}

Answer the user's question using
the retrieved agricultural knowledge.

Rules:

1. Focus on the predicted disease.
2. Give a simple farmer-friendly answer.
3. Do not invent unsupported information.
4. Explain symptoms, causes,
   prevention or treatment when relevant.
"""


        # ----------------------------------------------------
        # GENERATE ANSWER
        # ----------------------------------------------------

        response = client.models.generate_content(

            model="gemini-3.5-flash",

            contents=prompt

        )


        return jsonify({

            "success": True,

            "answer":
                response.text

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        })


# ============================================================
# 12. CROP RECOMMENDATION
# ============================================================

@app.route(
    "/recommend",
    methods=["POST"]
)
def recommend():

    try:

        data = request.get_json()


        soil_type = data.get(
            "soil_type",
            ""
        )

        temperature = data.get(
            "temperature",
            ""
        )

        humidity = data.get(
            "humidity",
            ""
        )

        ph = data.get(
            "ph",
            ""
        )

        rainfall = data.get(
            "rainfall",
            ""
        )

        season = data.get(
            "season",
            ""
        )


        # ----------------------------------------------------
        # CREATE QUERY
        # ----------------------------------------------------

        query = f"""

Crop recommendation:

Soil Type:
{soil_type}

Temperature:
{temperature}

Humidity:
{humidity}

pH:
{ph}

Rainfall:
{rainfall}

Season:
{season}

"""


        # ----------------------------------------------------
        # EMBEDDING
        # ----------------------------------------------------

        embedding = create_embedding(
            query
        )


        # ----------------------------------------------------
        # RETRIEVE DOCUMENTS
        # ----------------------------------------------------

        documents = retrieve_documents(
            embedding
        )


        # ----------------------------------------------------
        # CREATE CONTEXT
        # ----------------------------------------------------

        context = ""

        for i, document in enumerate(
            documents
        ):

            content = document.get(
                "content",
                ""
            )

            context += (
                f"\nDocument {i + 1}:\n"
                f"{content}\n"
            )


        # ----------------------------------------------------
        # GEMINI PROMPT
        # ----------------------------------------------------

        prompt = f"""

You are an agriculture crop
recommendation assistant.

Farmer conditions:

Soil Type:
{soil_type}

Temperature:
{temperature}

Humidity:
{humidity}

pH:
{ph}

Rainfall:
{rainfall}

Season:
{season}

Retrieved Agricultural Knowledge:
{context}

Recommend suitable crops based
only on the retrieved knowledge.

For each suitable crop mention:

- Why it is suitable
- Fertilizer
- Harvest time
- Common diseases

Do not invent crops that are not
present in the retrieved knowledge.

Give a simple farmer-friendly answer.
"""


        # ----------------------------------------------------
        # GENERATE RECOMMENDATION
        # ----------------------------------------------------

        response = client.models.generate_content(

            model="gemini-3.5-flash",

            contents=prompt

        )


        return jsonify({

            "success": True,

            "recommendation":
                response.text

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        })


# ============================================================
# 13. RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("")
    print("--------------------------------")
    print("AGRICULTURE AI ASSISTANT")
    print("--------------------------------")
    print("Starting Flask server...")
    print("")

    app.run(
        debug=True
    )