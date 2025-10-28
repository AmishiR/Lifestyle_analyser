import streamlit as st
import joblib
import numpy as np
import google.generativeai as genai
import os 
import urllib.parse 
from dotenv import load_dotenv # <-- NEW: For loading .env file locally

# ---- Load Environment Variables ----
# This loads variables from the .env file in the local directory.
# For Streamlit Cloud deployment, this step is skipped, and it uses
# Streamlit Secrets (explained below).
load_dotenv() 

# ---- Gemini AI Setup ----
# Read the API key from the environment variable
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # This check handles both the missing .env (local) and missing secret (cloud)
    st.warning("🚨 GEMINI_API_KEY not found. AI-powered tips will be unavailable.")
    st.info("For local development, create a '.env' file. For Streamlit Cloud, use 'Secrets'.")
    gemini_available = False
else:
    try:
        # This is where the configuration happens if the key is present
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        gemini_available = True
        st.success("Fill the details and click 'Analyze My Lifestyle' to see tips.")

    except Exception as e:
        st.error(f"Could not initialize Gemini AI (Error: {e}). AI-powered tips will be unavailable.")
        gemini_available = False
# --- END NEW SECTION ---


# Load your trained model
model_file = "lifestyle.pkl"
if not os.path.exists(model_file):
    st.error(f"Error: '{model_file}' model file not found.")
    st.info("Please make sure 'lifestyle.pkl' is in the same directory as your Streamlit app.")
    st.stop() # Stop the app if the model is missing

try:
    model = joblib.load(model_file)
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()


# ---- BMI Calculation Function ----
def calculate_bmi(weight_kg, height_m):
    """Calculates Body Mass Index (BMI)."""
    if height_m > 0:
        return weight_kg / (height_m ** 2)
    return 0.0 # Return 0 or handle error if height is 0

# ---- Define your recommendation function ----
def health_recommendation_system(data):
    bmi = data['BMI']
    water = data['Water_Intake (liters)']
    workout = data['Workout_Frequency (days/week)']
    exercise_type = data['Physical exercise']
    meals = data['Daily meals frequency']

    score = 0
    recommendations = []

    # Simple scoring logic (you can replace with your actual function)
    score += (bmi / 10)
    score += water
    score += (workout * 0.5)
    score += (meals * 0.8)

    # Recommendations (replicating your Colab output)
    if bmi < 18.5:
        recommendations.append(f"🍽️ BMI ({bmi:.1f}) is **underweight**. Increase calorie intake with balanced protein meals.")
    elif bmi > 25:
        recommendations.append(f"⚖️ BMI ({bmi:.1f}) is **overweight**. Try a calorie deficit and regular exercise.")
    else:
        recommendations.append("✅ Maintain your current diet — your BMI is balanced.")

    if water < 2.5:
        recommendations.append(f"💧 Water intake ({water}L) is **low**. Increase to at least 2.5 liters daily.")
    else:
        recommendations.append("💦 Good hydration level maintained!")

    if workout < 3:
        recommendations.append(f"🚶‍♂️ Workout frequency ({workout} days) is **low**. Start exercising at least 3 times a week.")
    else:
        recommendations.append("🏋️ Keep up your regular workouts!")

    # Check for variety (assuming "balanced" is the ideal)
    if exercise_type not in ["balanced", "variety"]: # Added 'variety' as a possible good state
        recommendations.append(f"🧘 Your routine is focused on {exercise_type}. Add variety (cardio, flexibility, strength).")

    if meals < 3:
        recommendations.append(f"🍎 Eating {meals} meals/day. **Increase to 3–5 balanced meals** to stabilize metabolism.")

    return recommendations, round(score, 2)


# ---- Streamlit UI ----
st.set_page_config(page_title="Lifestyle Analysis", layout="wide")
st.title("🌿 Lifestyle Analysis Dashboard")
st.write("Analyze your habits and get personalized lifestyle recommendations 💡")

# --- Use columns for a cleaner layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Your Inputs")
    # --- BMI INPUTS (NEW) ---
    weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
    height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=175.0)
    height_m = height_cm / 100.0
    bmi = calculate_bmi(weight_kg, height_m)
    st.caption(f"Calculated BMI: **{bmi:.2f}**")
    # ------------------------
    
    water = st.number_input("Water Intake (liters/day)", min_value=0.0, max_value=5.0, value=1.0)
    workout = st.slider("Workout Frequency (days/week)", 0, 7, 1)
    exercise_type = st.selectbox("Primary Physical Exercise Type", ["cardio", "yoga", "strength", "balanced"]) # Added 'balanced'
    meals = st.slider("Daily Meals Frequency", 1, 6, 2)

# Encode exercise type same as Colab
exercise_map = {"cardio": 0, "yoga": 1, "strength": 2, "balanced": 3} # Added 'balanced'
encoded_exercise = exercise_map.get(exercise_type, 0) # Default to 0 if key not found

# Prepare features for prediction
# Ensure BMI is included in the features array
features = np.array([[bmi, water, workout, encoded_exercise, meals]])

# Create descriptive dict for recommendations
user_data = {
    'BMI': bmi,
    'Water_Intake (liters)': water,
    'Workout_Frequency (days/week)': workout,
    'Physical exercise': exercise_type,
    'Daily meals frequency': meals
}

# --- Results Area ---
with col2:
    st.subheader("🔍 Analysis Results")
    if st.button("Analyze My Lifestyle"):
        if bmi == 0.0:
             st.error("Please enter a valid height to calculate BMI and run the analysis.")
             st.stop()

        predicted_score = model.predict(features)[0]
        # Use the calculated BMI in the recommendation function
        recommendations, original_score = health_recommendation_system(user_data)

        st.success(f"Predicted Lifestyle Score: **{predicted_score:.2f}**")
        st.caption(f"Original Function Score (for comparison): **{original_score}**")

        st.divider()
        
        st.subheader("💡 Personalized Recommendations")
        for rec in recommendations:
            st.write(f"- {rec}")

        # ---- Gemini API Call ----
        st.divider()
        st.subheader("📺 Find Videos to Help You Start")
        st.caption("Click a link to search for videos on YouTube:")

        if gemini_available:
            with st.spinner("Finding relevant video searches..."):
                prompt = f"""
                You are a search assistant. A user has received lifestyle recommendations.
                Your ONLY task is to provide specific YouTube video search queries to help them act on these recommendations.

                **User's Data:**
                - BMI: {user_data['BMI']:.2f}
                - Water Intake: {user_data['Water_Intake (liters)']} liters/day
                - Workout Frequency: {user_data['Workout_Frequency (days/week)']} days/week
                - Exercise Type: {user_data['Physical exercise']}
                - Daily Meals: {user_data['Daily meals frequency']}

                **Recommendations Already Given:**
                {chr(10).join([f'- {r}' for r in recommendations])}

                **Your Task:**
                - Based *only* on the user's data and the recommendations, generate a list of 3-5 specific YouTube video search queries.
                - **Do not** provide any other text, advice, or motivational speech.
                - **Do not** number the list. Use *only* markdown bullets (e.g., `- Search query`).
                - Tailor the queries to the user's *specific problem*.
                - Be specific (e.g., "10-minute beginner workout" is better than "workout").

                **Example Output Format (use this format exactly):**
                - 15-minute beginner bodyweight workout
                - How to drink 3 liters of water a day
                - Healthy high-protein meal prep for the week
                """

                try:
                    response = gemini_model.generate_content(prompt)
                    
                    raw_queries_text = response.text
                    queries = raw_queries_text.split('\n') 
                    
                    for line in queries:
                        if line.strip().startswith('-'): 
                            query_text = line.strip().lstrip('-').strip()
                            if query_text: 
                                search_query_encoded = urllib.parse.quote_plus(query_text)
                                youtube_url = f"https://www.youtube.com/results?search_query={search_query_encoded}"
                                st.markdown(f"- [{query_text}]({youtube_url})")

                except Exception as e:
                    st.error(f"Error generating AI suggestions: {e}")
        else:
            st.warning("Gemini AI is not configured. Add your API key (line 16) to enable this feature.")
        # --- END MODIFIED SECTION ---

    else:
        st.info("Click the 'Analyze' button to see your results.")