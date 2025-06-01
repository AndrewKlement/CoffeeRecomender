from random import choices
import streamlit as st
from recommender import CoffeeRecommender

recommender = CoffeeRecommender('datasets/coffee_df_with_type_and_region.csv')

if 'page' not in st.session_state:
    st.session_state.page = 'select_user_type'

if st.session_state.page == 'select_user_type':
    st.title("Welcome to the Coffee Recommender!")
    st.markdown("Find the coffee that’s just right for you.")

    choices = {
        "I just want to find a coffee I’ll enjoy": "Beginner", 
        "I’m familiar with tasting notes and want to adjust detailed preferences": "Expert"
    }

    choice = st.radio("How would you like to get started?", choices.keys())
    if st.button("Continue"):
        st.session_state.user_type = choices[choice]
        st.session_state.page = 'recommend'
        st.rerun()

elif st.session_state.page == 'recommend':
    if st.session_state.user_type == "Beginner":
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
                roast_map = {"Light": 0.5, "Medium": 0.3, "Dark": 0.0}
            else:
                roast_map = {"Light": 1, "Medium": 0.75, "Dark": 0.5}

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

            flavor_keywords = {
                "Fruity": ["acid"],
                "Nutty": ["flavor", "aftertaste"],
                "Chocolatey": ["body", "flavor"],
                "Floral": ["aroma", "flavor"],
                "Earthy": ["aftertaste", "body"]
            }

            for note in flavor_profile:
                for feat in flavor_keywords.get(note, []):
                    mapped_prefs[feat] = max(mapped_prefs.get(feat, 0.5), 0.7)

            alpha = 0.3 
            if desc == '':
                if not flavor_profile:
                    recommendations = recommender.recommend(mapped_prefs, desc, alpha=1)
                else:
                    recommendations = recommender.recommend(mapped_prefs, " ".join(flavor_profile), alpha=alpha)
            else:
                recommendations = recommender.recommend(mapped_prefs, desc, alpha=alpha)

            st.header("Top Coffee Recommendations:")
            for idx, row in recommendations.iterrows():
                st.markdown(f"### {row['name']} from {row['origin']}")
                st.markdown(f"- **Roast:** {row['roast']}  |  **Flavor:** {row['flavor']:.2f}")
                st.markdown(f"- **Aroma:** {row['aroma']:.2f}  |  **With Milk:** {'Yes' if row['with_milk'] > 0.5 else 'No'}")
                st.markdown(f"**Description:** {row['desc_1']}")
                st.markdown("---")

    else:
        st.markdown("### Adjust your coffee preferences with sliders")
        user_prefs = {}
        for f in recommender.features:
            label = 'Roast level' if f == 'agtron' else f.capitalize()
            user_prefs[f] = st.slider(label, 0.0, 1.0, 0.5)

        user_text = st.text_area("Describe the coffee you want (flavor, aroma, etc.)", "")
        alpha = 0.5

        if st.button("Recommend Coffee"):
            if user_text.strip() == "":
                st.warning("Please enter a description to improve recommendations!")
            else:
                user_prefs['agtron'] = 1 - user_prefs['agtron']
                results = recommender.recommend(user_prefs, user_text, alpha=alpha)
                for idx, row in results.iterrows():
                    st.markdown(f"### {row['name']} from {row['origin']}")
                    st.markdown(f"- **Roast:** {row['roast']}  |  **Acidity:** {row['acid']:.2f}  |  **Flavor:** {row['flavor']:.2f}")
                    st.markdown(f"- **Body:** {row['body']:.2f}  |  **Aroma:** {row['aroma']:.2f}  |  **Aftertaste:** {row['aftertaste']:.2f}")
                    st.markdown(f"- **With Milk:** {'Yes' if row['with_milk'] > 0.5 else 'No'}")
                    st.markdown(f"**Description:** {row['desc_1']}")
                    st.markdown("---")