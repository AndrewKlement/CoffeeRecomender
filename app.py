from random import choices
import streamlit as st
from recommender import CoffeeRecommender

recommender = CoffeeRecommender('datasets/coffee_df_with_type_and_region.csv')

if 'page' not in st.session_state:
    st.session_state.page = 'select_user_type'

if st.session_state.page == 'select_user_type':
    st.title("Welcome to the Coffee Recommender!")
    st.markdown("Find the coffee that’s just right for you.")

    choices_map = {
        "I just want to find a coffee I’ll enjoy": "Beginner",
        "I’m familiar with tasting notes and want to adjust detailed preferences": "Expert"
    }

    choice = st.radio("How would you like to get started?", list(choices_map.keys()))
    if st.button("Continue"):
        st.session_state.user_type = choices_map[choice]
        st.session_state.page = 'recommend'
        st.rerun()

elif st.session_state.page == 'recommend':
    # Input budget per 100g before any recommendations
    min_price = float(recommender.df['price_per_100g'].min())
    max_price = float(recommender.df['price_per_100g'].max())

    if st.session_state.user_type == "Beginner":
        st.markdown("### Answer a few quick questions")

        roast = st.radio("How do you like your roast?", ["Light", "Medium", "Dark"])
        flavor_profile = st.multiselect(
            "Which flavor notes do you enjoy?",
            ["Fruity", "Nutty", "Chocolatey", "Floral", "Earthy"]
        )
        with_milk = st.radio("Do you usually drink coffee with milk?", ["Yes", "No"])
        strength = st.radio("How strong do you like your coffee?", ["Mild", "Medium", "Strong"])
        max_budget = st.number_input(
            "Max budget per 100 g (USD)",
            min_value=min_price,
            max_value=max_price,
            value=max_price,
            step=0.5
        )
        desc = st.text_area("Anything else you'd like to add?", "")

        if st.button("Recommend Coffee"):
            roast_map = {"Light": 0.5, "Medium": 0.3, "Dark": 0.0} if with_milk == "Yes" else {"Light": 1, "Medium": 0.75, "Dark": 0.5}
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
                    recs = recommender.recommend(mapped_prefs, desc, alpha=1, max_budget_100g=max_budget)
                else:
                    recs = recommender.recommend(mapped_prefs, " ".join(flavor_profile), alpha=alpha, max_budget_100g=max_budget)
            else:
                recs = recommender.recommend(mapped_prefs, desc, alpha=alpha, max_budget_100g=max_budget)

            st.header("Top Coffee Recommendations:")
            for _, row in recs.iterrows():
                st.markdown(f"### {row['name']} from {row['origin']}")
                st.markdown(
                    f"- **Roast:** {row['roast']}  |  **Acidity:** {row['acid']:.2f}  |  **Flavor:** {row['flavor']:.2f}\n"
                    f"- **Body:** {row['body']:.2f}  |  **Aroma:** {row['aroma']:.2f}  |  **Aftertaste:** {row['aftertaste']:.2f}"
                )
                st.markdown(f"**Price per 100g:** ${row['price_per_100g']:.2f}")
                st.markdown(f"**Description:** {row['desc_1']}")
                st.markdown("---")

    else:
        st.markdown("### Adjust your coffee preferences with sliders")
        user_prefs = {f: st.slider('Roast level' if f=='agtron' else f.capitalize(), 0.0, 1.0, 0.5) for f in recommender.features}
        max_budget = st.number_input(
            "Max budget per 100 g (USD)",
            min_value=min_price,
            max_value=max_price,
            value=max_price,
            step=0.5
        )
        user_text = st.text_area("Describe the coffee you want (flavor, aroma, etc.)", "")
        alpha = 0.5

        if st.button("Recommend Coffee"):
            if user_text.strip() == "":
                st.warning("Please enter a description to improve recommendations!")
            else:
                user_prefs['agtron'] = 1 - user_prefs['agtron']
                recs = recommender.recommend(user_prefs, user_text, alpha=alpha, max_budget_100g=max_budget)
                st.header("Top Coffee Recommendations:")
                for _, row in recs.iterrows():
                    st.markdown(f"### {row['name']} from {row['origin']}")
                    st.markdown(
                        f"- **Roast:** {row['roast']}  |  **Acidity:** {row['acid']:.2f}  |  **Flavor:** {row['flavor']:.2f}\n"
                        f"- **Body:** {row['body']:.2f}  |  **Aroma:** {row['aroma']:.2f}  |  **Aftertaste:** {row['aftertaste']:.2f}"
                    )
                    st.markdown(f"**Price per 100g:** ${row['price_per_100g']:.2f}")
                    st.markdown(f"**Description:** {row['desc_1']}")
                    st.markdown("---")
