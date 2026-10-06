import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import database.db as db

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

def calculate_product_risk(product_id):
    """
    Calculates AI Risk Score (0-100) and Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
    Uses scikit-learn IsolationForest when historical data exists, 
    combined with a transparent heuristic rule scoring engine.
    """
    logs = db.get_verification_logs(product_id=product_id, limit=200)
    
    if not logs:
        return {
            "product_id": product_id,
            "risk_score": 5.0,
            "risk_level": "LOW",
            "reason": "No verification history recorded yet. Normal initial baseline.",
            "model_version": "v1.0-rule-baseline",
            "total_attempts": 0,
            "failed_attempts": 0,
            "distinct_devices": 0,
            "failure_rate": 0.0
        }

    df = pd.DataFrame(logs)
    total_attempts = len(df)
    failed_attempts = len(df[df['verification_status'].isin(['INCORRECT_CODE', 'INVALID_REFERENCE', 'SUSPICIOUS'])])
    successful_attempts = len(df[df['verification_status'] == 'VERIFIED'])
    
    failure_rate = (failed_attempts / total_attempts) * 100.0 if total_attempts > 0 else 0.0
    
    distinct_devices = df['device_information'].nunique() if 'device_information' in df.columns else 1

    # Frequency analysis - attempts in last 1 hour
    df['dt'] = pd.to_datetime(df['timestamp'], errors='coerce')
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    recent_1h_attempts = len(df[df['dt'] >= one_hour_ago])
    recent_24h_attempts = len(df[df['dt'] >= twenty_four_hours_ago])

    # --- 1. Rule-Based Heuristic Scoring ---
    heuristic_score = 0.0
    reasons = []

    # Failure rate penalty
    if failure_rate > 75:
        heuristic_score += 35.0
        reasons.append(f"Extremely high failed verification rate ({failure_rate:.1f}%)")
    elif failure_rate > 50:
        heuristic_score += 25.0
        reasons.append(f"High failed verification rate ({failure_rate:.1f}%)")
    elif failure_rate > 25:
        heuristic_score += 15.0
        reasons.append(f"Moderate failed verification rate ({failure_rate:.1f}%)")

    # Velocity / Frequency spike penalty
    if recent_1h_attempts >= 10:
        heuristic_score += 30.0
        reasons.append(f"Unusual high-frequency velocity ({recent_1h_attempts} scans in past hour)")
    elif recent_1h_attempts >= 5:
        heuristic_score += 18.0
        reasons.append(f"Elevated scanning frequency ({recent_1h_attempts} scans in past hour)")

    # Multiple distinct devices penalty (cloned QR distribution risk)
    if distinct_devices >= 8 and total_attempts < 30:
        heuristic_score += 25.0
        reasons.append(f"High device diversity ({distinct_devices} unique devices scanned across few units)")
    elif distinct_devices >= 4:
        heuristic_score += 10.0
        reasons.append(f"Multiple distinct devices recorded ({distinct_devices} devices)")

    # Total consecutive failures penalty
    if failed_attempts >= 5:
        heuristic_score += 15.0
        reasons.append(f"Multiple failed code attempts recorded ({failed_attempts} total failures)")

    # --- 2. Isolation Forest Anomaly Detection (if scikit-learn & sufficient samples) ---
    isolation_anomaly_score = 0.0
    model_ver = "v1.0-rule-engine"

    if SKLEARN_AVAILABLE and total_attempts >= 10:
        try:
            # Extract features for anomaly model
            # Features: [failed_count, total_count, failure_rate, distinct_devices, recent_1h]
            X = np.array([[
                failed_attempts,
                total_attempts,
                failure_rate,
                distinct_devices,
                recent_1h_attempts
            ]])
            
            # Standard baseline reference matrix for training IsolationForest
            synthetic_normal = np.array([
                [0, 3, 0.0, 1, 1],
                [0, 5, 0.0, 2, 2],
                [1, 6, 16.6, 2, 1],
                [0, 10, 0.0, 3, 2],
                [1, 12, 8.3, 3, 1],
                [2, 15, 13.3, 4, 3],
                [10, 12, 83.3, 8, 10], # Anomaly sample
                [8, 10, 80.0, 6, 8]   # Anomaly sample
            ])
            
            model = IsolationForest(n_estimators=50, contamination=0.2, random_state=42)
            model.fit(synthetic_normal)
            
            # Predict anomaly (-1 for anomaly, 1 for normal)
            pred = model.predict(X)[0]
            raw_score = model.score_samples(X)[0] # lower score means more anomalous
            
            # Map raw score (-0.8 to -0.3) to 0-30 penalty
            isolation_anomaly_score = max(0.0, (0.0 - raw_score) * 40.0) if pred == -1 else 0.0
            model_ver = "v1.0-isolation-forest-hybrid"
            
            if pred == -1:
                reasons.append("Isolation Forest detected statistical anomaly pattern in scan telemetry")

        except Exception as e:
            print(f"ML IsolationForest scoring error: {e}")

    # Combine scores & constrain to 0 - 100
    final_score = min(100.0, max(0.0, heuristic_score + isolation_anomaly_score))
    
    # Determine Risk Level
    if final_score <= 30.0:
        risk_level = "LOW"
    elif final_score <= 60.0:
        risk_level = "MEDIUM"
    elif final_score <= 80.0:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    if not reasons:
        reasons.append("Normal verification activity within expected baseline thresholds.")

    return {
        "product_id": product_id,
        "risk_score": round(final_score, 1),
        "risk_level": risk_level,
        "reason": " | ".join(reasons),
        "reasons_list": reasons,
        "model_version": model_ver,
        "total_attempts": total_attempts,
        "failed_attempts": failed_attempts,
        "successful_attempts": successful_attempts,
        "distinct_devices": distinct_devices,
        "failure_rate": round(failure_rate, 1),
        "recent_1h_attempts": recent_1h_attempts,
        "recent_24h_attempts": recent_24h_attempts
    }
