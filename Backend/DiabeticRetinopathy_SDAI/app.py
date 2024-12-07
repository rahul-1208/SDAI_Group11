from fastapi import FastAPI, HTTPException, File, UploadFile
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import io
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your .h5 model
model = tf.keras.models.load_model("diabetic_retinopathy_v3.h5")  # Update with the correct model path

# Define a mapping for prediction classes (adjust based on your model's output)
severity_map = {0: "No Retinopathy", 1: "Mild", 2: "Moderate", 3: "Severe", 4: "Proliferative"}

# Preprocessing function for images
def preprocess_image(image: Image.Image):
    """
    Preprocess the image to match the model's input requirements.
    """
    img_resized = image.resize((224, 224))  # Update size based on your model input dimensions
    img_array = img_to_array(img_resized) / 255.0  # Normalize pixel values to [0, 1]
    return np.expand_dims(img_array, axis=0)  # Add batch dimension

@app.post("/predict-image")
async def predict_image(file: UploadFile = File(...)):
    """
    Predict the severity of diabetic retinopathy from an uploaded image.
    """
    try:
        # Read and open the uploaded image
        image = Image.open(io.BytesIO(await file.read()))
        
        # Preprocess the image
        input_array = preprocess_image(image)
        
        # Predict using the model
        predictions = model.predict(input_array)
        predicted_class = np.argmax(predictions, axis=1)[0]
         # Get the confidence score (the probability of the predicted class)
        confidence_score = np.max(predictions, axis=1)[0]
        severity = severity_map.get(predicted_class, "Unknown")
        
        return {
            "severity": severity,
            "raw_prediction": int(predicted_class),
            "probabilities": predictions.tolist(),
            "confidence_score": float(confidence_score)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
