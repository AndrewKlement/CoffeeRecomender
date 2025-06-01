import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CoffeeRecommender:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.features = ["agtron", "aroma", "acid", "body", "flavor", "aftertaste"]
        
        self.df['full_desc'] = self.df[['desc_1', 'desc_2', 'desc_3']].fillna('').agg(' '.join, axis=1)
        self.df['full_desc'] = self.df['full_desc'].apply(self.__preprocess_description)

        self.df["agtron"] = self.df["agtron"].apply(self.__convert_to_float)
        self.df.dropna(subset=self.features, inplace=True)

        self.scaler = MinMaxScaler()
        self.df[self.features] = self.scaler.fit_transform(self.df[self.features])

        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.desc_tfidf = self.vectorizer.fit_transform(self.df['full_desc'])

    def __convert_to_float(self, val):
        if isinstance(val, str) and '/' in val:
            try:
                num, denom = val.split('/')
                return float(num) / float(denom)
            except:
                return None
        try:
            return float(val)
        except:
            return None

    def __preprocess_description(self, text):
        text = text.lower().strip()

        patterns_to_remove = [
            r"^i (would like|want|am looking|feel like)( to)?( have| try| taste| get)?( a| some)?",
            r"^i (need|prefer|love|crave)( a| some)?",
            r"^looking for( a| some)?",
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text)

        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def recommend(self, user_prefs, user_text, top_n=5, alpha=0.5):
        clean_text = self.__preprocess_description(user_text)

        user_vector = np.array([user_prefs[f] for f in self.features])
        coffee_features = self.df[self.features].values

        distances = np.linalg.norm(coffee_features - user_vector, axis=1)
        dist_norm = (distances - distances.min()) / (distances.max() - distances.min())
        numeric_sim = 1 - dist_norm

        user_vec = self.vectorizer.transform([clean_text])
        text_sim = cosine_similarity(user_vec, self.desc_tfidf).flatten()

        combined_sim = alpha * numeric_sim + (1 - alpha) * text_sim

        results = self.df.copy()
        results['combined_sim'] = combined_sim

        return results.sort_values('combined_sim', ascending=False).head(top_n)
