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

        def _parse_price(s):
            s = str(s)
            # Cari dua angka yang dipisah slash, abaikan teks apa pun di sekitarnya
            m = re.search(r"(\d+(?:\.\d+)?)[^0-9/]*\/\s*(\d+(?:\.\d+)?)(?:\s*([A-Za-z]+))?", s)
            if not m:
                return np.nan

            price = float(m.group(1))       # harga (misal 350 atau 400)
            qty   = float(m.group(2))       # kuantitas (misal 227 atau 4)
            unit  = m.group(3).lower() if m.group(3) else 'g'

            # Konversi ke gram
            if 'oz' in unit or 'ounce' in unit:
                qty_g = qty * 28.3495
            else:
                # anggap 'g', 'gram', atau unit tak dikenal = gram
                qty_g = qty

            # Harga per 100g
            return price / qty_g * 100

        self.df['price_per_100g'] = self.df['est_price'].apply(_parse_price)


        self.df['full_desc'] = self.df[['desc_1', 'desc_2', 'desc_3']].fillna('').agg(' '.join, axis=1)
        self.df['full_desc'] = self.df['full_desc'].apply(self.__preprocess_description)

        self.df["agtron"] = self.df["agtron"].apply(self.__convert_to_float)
        self.df.dropna(subset=self.features, inplace=True)

        # Reset index to align with TF-IDF matrix rows
        self.df.reset_index(drop=True, inplace=True)

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

    def recommend(self, user_prefs, user_text, top_n=5, alpha=0.5, max_budget_100g=None):
        # Filter by budget if specified
        df = self.df
        if max_budget_100g is not None:
            df = df[df['price_per_100g'] <= max_budget_100g]
        if df.empty:
            return pd.DataFrame()

        # Numeric similarity
        user_vec = np.array([user_prefs[f] for f in self.features])
        feats = df[self.features].values
        dists = np.linalg.norm(feats - user_vec, axis=1)
        norm_d = (dists - dists.min()) / (dists.max() - dists.min())
        sim_num = 1 - norm_d

        # Text similarity
        clean_text = self.__preprocess_description(user_text)
        user_tfidf = self.vectorizer.transform([clean_text])
        sim_text = cosine_similarity(user_tfidf, self.desc_tfidf[df.index]).flatten()

        # Combine and return top N
        df = df.copy()
        df['combined_sim'] = alpha * sim_num + (1 - alpha) * sim_text
        return df.sort_values('combined_sim', ascending=False).head(top_n)
