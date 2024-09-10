import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import silhouette_score
from scipy.stats import zscore

class AnomalyDetector:
    def __init__(self, contamination=0.1, n_estimators=100):
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(contamination=contamination, n_estimators=n_estimators, random_state=42)
        self.kmeans = None
        self.dbscan = None
        self.history = []
        self.threshold = 2.5  # Z-score threshold for anomalies

    def fit(self, features):
        scaled_features = self.scaler.fit_transform(features)
        
        # Fit Isolation Forest
        self.iforest.fit(scaled_features)
        
        # Determine optimal number of clusters for KMeans
        n_clusters = self._optimal_clusters(scaled_features)
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.kmeans.fit(scaled_features)
        
        # Fit DBSCAN
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.dbscan.fit(scaled_features)

    def _optimal_clusters(self, data, max_clusters=10):
        silhouette_scores = []
        for n in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n, random_state=42)
            labels = kmeans.fit_predict(data)
            score = silhouette_score(data, labels)
            silhouette_scores.append(score)
        return silhouette_scores.index(max(silhouette_scores)) + 2

    def detect_anomalies(self, features):
        if self.kmeans is None or self.dbscan is None:
            raise ValueError("Model not fitted. Call fit() first.")

        scaled_features = self.scaler.transform(features)
        
        # Isolation Forest anomalies
        iforest_anomalies = self.iforest.predict(scaled_features) == -1
        
        # KMeans anomalies (points far from cluster centers)
        distances = self.kmeans.transform(scaled_features)
        kmeans_anomalies = np.min(distances, axis=1) > np.percentile(np.min(distances, axis=1), 95)
        
        # DBSCAN anomalies
        dbscan_anomalies = self.dbscan.fit_predict(scaled_features) == -1
        
        # Combine anomalies
        combined_anomalies = iforest_anomalies | kmeans_anomalies | dbscan_anomalies
        
        # Apply adaptive thresholding
        self.history.extend(features[combined_anomalies])
        if len(self.history) > 1000:  # Limit history to last 1000 anomalies
            self.history = self.history[-1000:]
        
        if len(self.history) > 10:  # Need some history for Z-score
            z_scores = zscore(self.history, axis=0)
            adaptive_anomalies = np.any(np.abs(z_scores) > self.threshold, axis=1)
            combined_anomalies[combined_anomalies] = adaptive_anomalies
        
        return combined_anomalies

    def partial_fit(self, features, anomalies):
        # Update the model with new data
        scaled_features = self.scaler.transform(features)
        self.iforest.partial_fit(scaled_features[~anomalies])  # Only fit on non-anomalous data
        
        # Periodically re-fit KMeans and DBSCAN
        if np.random.random() < 0.1:  # 10% chance to re-fit
            self.fit(features)

def evaluate_model(model, X_train, X_test, contamination=0.1):
    model.fit(X_train)
    y_pred = model.detect_anomalies(X_test)
    
    # Simulate some known anomalies in test set
    n_anomalies = int(contamination * len(X_test))
    true_anomalies = np.zeros(len(X_test), dtype=bool)
    true_anomalies[:n_anomalies] = True
    np.random.shuffle(true_anomalies)
    
    tp = np.sum(y_pred & true_anomalies)
    fp = np.sum(y_pred & ~true_anomalies)
    tn = np.sum(~y_pred & ~true_anomalies)
    fn = np.sum(~y_pred & true_anomalies)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return precision, recall, f1_score

if __name__ == "__main__":
    # Generate sample data with anomalies
    n_samples = 1000
    n_features = 10
    X = np.random.randn(n_samples, n_features)
    
    # Add some anomalies
    X[:50] += np.random.uniform(5, 10, size=(50, n_features))
    
    # Split data
    X_train, X_test = train_test_split(X, test_size=0.3, random_state=42)
    
    # Create and evaluate model
    detector = AnomalyDetector()
    precision, recall, f1_score = evaluate_model(detector, X_train, X_test)
    
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1-score: {f1_score:.2f}")
    
    # Test adaptability
    print("\nTesting adaptability...")
    for i in range(5):
        new_data = np.random.randn(100, n_features)
        if i % 2 == 0:
            new_data += np.random.uniform(5, 10, size=(100, n_features))
        anomalies = detector.detect_anomalies(new_data)
        detector.partial_fit(new_data, anomalies)
        print(f"Iteration {i+1}: Detected {np.sum(anomalies)} anomalies out of 100 samples")