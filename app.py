import streamlit as st
from recommender import CoffeeRecommender

# Load recommender
recommender = CoffeeRecommender('datasets/coffee_df_with_type_and_region.csv')

# State control
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

st.title("☕ Hybrid Coffee Recommender")

# --- PAGE 1: EXPERT CHECK ---
if st.session_state.user_type is None:
    st.markdown("### Are you a coffee expert?")
    if st.button("I'm an Expert"):
        st.session_state.user_type = 'expert'
        st.rerun()
    elif st.button("I'm Not Sure / Beginner"):
        st.session_state.user_type = 'beginner'
        st.rerun()

# --- PAGE 2A: EXPERT UI ---
elif st.session_state.user_type == 'expert':
    st.markdown("### Adjust your coffee preferences with sliders")
    user_prefs = {}
    for f in recommender.features:
        label = 'Roast level' if f == 'agtron' else f.capitalize()
        user_prefs[f] = st.slider(label, 0.0, 1.0, 0.5)

    user_text = st.text_area("Describe the coffee you want (flavor, aroma, etc.)", "")
    alpha = st.slider("Preference weight: 1 = only sliders, 0 = only description", 0.0, 1.0, 0.5)

    if st.button("Recommend Coffee"):
        if user_text.strip() == "":
            st.warning("Please enter a description to improve recommendations!")
        else:
            results = recommender.recommend(user_prefs, user_text, alpha=alpha)
            for idx, row in results.iterrows():
                st.markdown(f"### {row['name']} from {row['origin']}")
                st.markdown(f"- **Roast:** {row['roast']}  |  **Acidity:** {row['acid']:.2f}  |  **Flavor:** {row['flavor']:.2f}")
                st.markdown(f"- **Body:** {row['body']:.2f}  |  **Aroma:** {row['aroma']:.2f}  |  **Aftertaste:** {row['aftertaste']:.2f}")
                st.markdown(f"- **With Milk:** {'Yes' if row['with_milk'] > 0.5 else 'No'}")
                st.markdown(f"**Description:** {row['full_desc'][:300]}...")
                st.markdown("---")

# --- PAGE 2B: BEGINNER UI ---
elif st.session_state.user_type == 'beginner':
    st.markdown("### Answer a few quick questions")

    roast = st.radio("How do you like your roast?", ["Light", "Medium", "Dark"])
    
    flavor_profile = st.multiselect(
        "Which flavor notes do you enjoy?",
        ["Fruity", "Nutty", "Chocolatey", "Floral", "Earthy"]
    )

    with_milk = st.radio("Do you usually drink coffee with milk?", ["Yes", "No"])
    
    strength = st.radio("How strong do you like your coffee?", ["Mild", "Medium", "Strong"])

    desc = st.text_area("Anything else you'd like to add?", "")

    if st.button("Recommend Coffee"):

        if with_milk == "Yes":
            roast_map = {"Light": 0.7, "Medium": 0.4, "Dark": 0.1}
        else:
            roast_map = {"Light": 0.8, "Medium": 0.5, "Dark": 0.2}

        strength_map = {"Mild": 0.3, "Medium": 0.5, "Strong": 0.8}

        mapped_prefs = {
            "agtron": roast_map[roast],
            "with_milk": 1.0 if with_milk == "Yes" else 0.0,
            "body": strength_map[strength],
            "acid": 0.6 if "Fruity" in flavor_profile else 0.4,
            "flavor": 0.7,
            "aroma": 0.6,
            "aftertaste": 0.5
        }

        # Optional: boost features based on flavor profile
        flavor_keywords = {
            "Fruity": ["acid"],
            "Nutty": ["flavor", "aftertaste"],
            "Chocolatey": ["body", "flavor"],
            "Floral": ["aroma"],
            "Earthy": ["aftertaste", "body"]
        }

        for note in flavor_profile:
            for feat in flavor_keywords.get(note, []):
                mapped_prefs[feat] = max(mapped_prefs.get(feat, 0.5), 0.7)

        alpha = 0.3 
        recommendations = recommender.recommend(mapped_prefs, desc, alpha=alpha)

        st.header("Top Coffee Recommendations:")
        for idx, row in recommendations.iterrows():
            st.markdown(f"### {row['name']} from {row['origin']}")
            st.markdown(f"- **Roast:** {row['roast']}  |  **Flavor:** {row['flavor']:.2f}")
            st.markdown(f"- **Aroma:** {row['aroma']:.2f}  |  **With Milk:** {'Yes' if row['with_milk'] > 0.5 else 'No'}")
            st.markdown(f"**Description:** {row['full_desc'][:300]}...")
            st.markdown("---")
