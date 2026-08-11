// ============================================================
// AGRICULTURE AI ASSISTANT
// FRONTEND JAVASCRIPT
// ============================================================


// ============================================================
// 1. IMAGE PREVIEW
// ============================================================

const imageInput = document.getElementById("imageInput");

const imagePreview = document.getElementById(
    "imagePreview"
);


if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            const file = this.files[0];

            if (file) {

                const imageURL =
                    URL.createObjectURL(file);

                imagePreview.src =
                    imageURL;

                imagePreview.style.display =
                    "block";
            }

        }
    );
}


// ============================================================
// 2. DISEASE PREDICTION
// ============================================================

async function predictDisease() {

    const fileInput =
        document.getElementById(
            "imageInput"
        );

    const resultCard =
        document.getElementById(
            "predictionResult"
        );

    const chatSection =
        document.getElementById(
            "chatSection"
        );


    // Check image

    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        alert(
            "Please select a plant leaf image first."
        );

        return;
    }


    const file =
        fileInput.files[0];


    // Create FormData

    const formData =
        new FormData();

    formData.append(
        "image",
        file
    );


    // Show loading

    const button =
        document.querySelector(
            ".upload-area .primary-button"
        );

    const originalText =
        button.innerText;

    button.innerText =
        "🔄 Analyzing...";

    button.disabled =
        true;


    try {

        // Send image to Flask

        const response =
            await fetch(
                "/predict",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        // Check result

        if (!data.success) {

            alert(
                data.message ||
                "Prediction failed."
            );

            return;
        }


        // Display disease

        document.getElementById(
            "diseaseName"
        ).innerText =
            data.disease;


        // Display confidence

        document.getElementById(
            "confidenceValue"
        ).innerText =
            data.confidence + "%";


        // Show result

        resultCard.style.display =
            "block";


        // Show chat

        chatSection.style.display =
            "block";


        // Store disease

        window.predictedDisease =
            data.disease;


        // Scroll to result

        resultCard.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


    }

    catch (error) {

        console.error(
            "Prediction error:",
            error
        );

        alert(
            "Unable to connect to the Flask server."
        );

    }

    finally {

        button.innerText =
            originalText;

        button.disabled =
            false;
    }
}


// ============================================================
// 3. ASK ABOUT DISEASE
// ============================================================

async function askDisease() {

    const questionInput =
        document.getElementById(
            "questionInput"
        );

    const answerBox =
        document.getElementById(
            "answerBox"
        );


    const question =
        questionInput.value.trim();


    // Check question

    if (!question) {

        alert(
            "Please enter your question."
        );

        return;
    }


    // Check prediction

    if (!window.predictedDisease) {

        alert(
            "Please predict the disease first."
        );

        return;
    }


    // Show loading

    answerBox.style.display =
        "block";

    answerBox.innerText =
        "🔄 Searching agricultural knowledge and generating answer...";


    try {

        const response =
            await fetch(
                "/ask",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        question:
                            question,

                        disease:
                            window.predictedDisease

                    })

                }
            );


        const data =
            await response.json();


        // Check result

        if (!data.success) {

            answerBox.innerText =
                "❌ " +
                (
                    data.message ||
                    "Unable to generate answer."
                );

            return;
        }


        // Display answer

        answerBox.innerText =
            data.answer;


    }

    catch (error) {

        console.error(
            "Chat error:",
            error
        );

        answerBox.innerText =
            "❌ Unable to connect to the Flask server.";

    }
}


// ============================================================
// 4. CROP RECOMMENDATION
// ============================================================

async function recommendCrops() {

    const soilType =
        document.getElementById(
            "soilType"
        ).value.trim();


    const temperature =
        document.getElementById(
            "temperature"
        ).value.trim();


    const humidity =
        document.getElementById(
            "humidity"
        ).value.trim();


    const ph =
        document.getElementById(
            "ph"
        ).value.trim();


    const rainfall =
        document.getElementById(
            "rainfall"
        ).value.trim();


    const season =
        document.getElementById(
            "season"
        ).value.trim();


    const cropResult =
        document.getElementById(
            "cropResult"
        );


    const cropAnswer =
        document.getElementById(
            "cropAnswer"
        );


    // Check fields

    if (
        !soilType ||
        !temperature ||
        !humidity ||
        !ph ||
        !rainfall ||
        !season
    ) {

        alert(
            "Please fill in all crop recommendation fields."
        );

        return;
    }


    // Show loading

    cropResult.style.display =
        "block";

    cropAnswer.innerText =
        "🔄 Searching crop knowledge and generating recommendations...";


    try {

        const response =
            await fetch(
                "/recommend",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        soil_type:
                            soilType,

                        temperature:
                            temperature,

                        humidity:
                            humidity,

                        ph:
                            ph,

                        rainfall:
                            rainfall,

                        season:
                            season

                    })

                }
            );


        const data =
            await response.json();


        // Check result

        if (!data.success) {

            cropAnswer.innerText =
                "❌ " +
                (
                    data.message ||
                    "Unable to generate recommendations."
                );

            return;
        }


        // Display recommendation

        cropAnswer.innerText =
            data.recommendation;


        // Scroll to result

        cropResult.scrollIntoView({

            behavior: "smooth",

            block: "center"

        });


    }

    catch (error) {

        console.error(
            "Crop recommendation error:",
            error
        );

        cropAnswer.innerText =
            "❌ Unable to connect to the Flask server.";

    }
}