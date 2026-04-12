import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


class MusicClusterer:
    def __init__(self, n_clusters = 5):
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(
            max_features=500, 
            stop_words='english'
        )
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)

    def process(self, tracks):
        if not tracks:
                return []
        data = []
        for t in tracks:
            tags_str = " ".join(t.get('tags', []))
            data.append(tags_str if tags_str.strip() else "unknown")

        matrix = self.vectorizer.fit_transform(data)

        clusters = self.model.fit_predict(matrix)

        for i, track in enumerate(tracks):
            track['cluster'] = int(clusters[i])

        return tracks

    def get_cluster_keywords(self):
        order_centroids = self.model.cluster_centers_.argsort()[:, ::-1]
        terms = self.vectorizer.get_feature_names_out()
        
        keywords = {}
        for i in range(self.n_clusters):
            top_terms = [terms[ind] for ind in order_centroids[i, :5]]
            keywords[i] = top_terms
        return keywords