import streamlit as st
import joblib
import numpy as np
import google.generativeai as genai
import os # Added for checking file existence

# ---- Gemini AI Setup ----
# WARNING: Do NOT share this code or commit it to GitHub with your key!
# This method is ONLY for your local development.
# ---- Gemini AI Setup (Corrected) ----
try:
    # --- PASTE YOUR KEY HERE ---
    # NOTE: The check below is now only for the placeholder string.
    api_key = "AIzaSyD51MMvCEFoqk0Z9ww_uKvFRRY2WMreZiA" # <- Your actual key should be here
    # ---------------------------
    
    # Define the placeholder value for a cleaner check
    PLACEHOLDER_KEY = "AIzaSyBcIG9pJ28EiYFrjBuFab9QhdKoTd5fyxU"

    if api_key == PLACEHOLDER_KEY:
        st.warning("Please add your Gemini API key (line 16) to the script to enable AI-powered tips.")
        gemini_available = False
    else:
        # This is where the configuration happens if the key is present
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        gemini_available = True
        st.success("Gemini AI is configured and ready! Click 'Analyze My Lifestyle' to see tips.")

except Exception as e:
    # This block catches configuration errors (e.g., bad key, network issue)
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
        recommendations.append("🍽️ Increase calorie intake with balanced protein meals (underweight).")
    elif bmi > 25:
        recommendations.append("⚖️ Try maintaining a calorie deficit and regular exercise (overweight).")
    else:
        recommendations.append("✅ Maintain your current diet — your BMI is balanced.")

    if water < 2.5:
        recommendations.append("💧 Increase water intake to at least 2.5 liters per day.")
    else:
        recommendations.append("💦 Good hydration level maintained!")

    if workout < 3:
        recommendations.append("🚶‍♂️ Start exercising at least 3 times a week.")
    else:
        recommendations.append("🏋️ Keep up your regular workouts!")

    # Check for variety (assuming "balanced" is the ideal)
    if exercise_type not in ["balanced", "variety"]: # Added 'variety' as a possible good state
        recommendations.append("🧘 Add variety — mix cardio, flexibility, and strength workouts.")

    if meals < 3:
        recommendations.append("🍎 Increase to 3–5 balanced meals daily to stabilize metabolism.")

    return recommendations, round(score, 2)


# ---- Streamlit UI ----
st.set_page_config(page_title="Lifestyle Analysis", layout="wide")
st.title("🌿 Lifestyle Analysis Dashboard")
st.write("Analyze your habits and get personalized lifestyle recommendations 💡")

# --- Use columns for a cleaner layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Your Inputs")
    # Collect user input (same as Colab)
    bmi = st.number_input("BMI", min_value=10.0, max_value=40.0, value=22.5)
    water = st.number_input("Water Intake (liters/day)", min_value=0.0, max_value=5.0, value=1.0)
    workout = st.slider("Workout Frequency (days/week)", 0, 7, 1)
    exercise_type = st.selectbox("Primary Physical Exercise Type", ["cardio", "yoga", "strength", "balanced"]) # Added 'balanced'
    meals = st.slider("Daily Meals Frequency", 1, 6, 2)

# Encode exercise type same as Colab
exercise_map = {"cardio": 0, "yoga": 1, "strength": 2, "balanced": 3} # Added 'balanced'
encoded_exercise = exercise_map.get(exercise_type, 0) # Default to 0 if key not found

# Prepare features for prediction
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
        predicted_score = model.predict(features)[0]
        recommendations, original_score = health_recommendation_system(user_data)

        st.success(f"Predicted Lifestyle Score: **{predicted_score:.2f}**")
        st.caption(f"Original Function Score (for comparison): **{original_score}**")

        st.divider()
        
        st.subheader("💡 Personalized Recommendations")
        for rec in recommendations:
            st.write(f"- {rec}")

        # ---- NEW: Gemini API Call ----
        st.divider()
        st.subheader("✨ AI-Powered Deeper Dive")

        if gemini_available:
            with st.spinner("Generating bonus AI tips..."):
                # Create a detailed prompt
                prompt = f"""
                You are a friendly and encouraging health and wellness coach.
                A user has provided their lifestyle data and received some basic recommendations.

                **User's Data:**
                - BMI: {user_data['BMI']}
                - Water Intake: {user_data['Water_Intake (liters)']} liters/day
                - Workout Frequency: {user_data['Workout_Frequency (days/week)']} days/week
                - Exercise Type: {user_data['Physical exercise']}
                - Daily Meals: {user_data['Daily meals frequency']}

                **Basic Recommendations Already Given:**
                {chr(10).join([f'- {r}' for r in recommendations])}

                **Your Task:**
                Based *only* on the data and recommendations above, provide 2-3 **new, specific, and actionable** tips to help them improve.
                - Be positive and motivational.
                - Suggest simple, practical things (e.g., specific food swaps, 5-minute activities).
                - **Importantly:** Suggest *types* of online videos or resources to search for (e.g., "Search on YouTube for '15-minute beginner bodyweight workout' or 'quick healthy meal prep for one'").
                - Do NOT repeat the recommendations already given. Focus on *supplementing* them.
                - Use markdown and emojis.
                """

                try:
                    response = gemini_model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error generating AI suggestions: {e}")
        else:
            st.warning("Gemini AI is not configured. Add your API key (line 16) to enable this feature.")
        # --- END NEW SECTION ---

    else:
        st.info("Click the 'Analyze' button to see your results.")