import pandas as pd
from datetime import datetime, timedelta
import database.db as db
from ml.anomaly_detector import calculate_product_risk

def get_system_ai_intelligence():
    """
    Aggregates full system verification intelligence and anomaly stats for Chart.js
    """
    products = db.get_all_products()
    logs = db.get_verification_logs(limit=500)
    
    product_risks = []
    high_risk_products = []
    suspicious_products = []
    
    total_risk_score_sum = 0.0
    
    for p in products:
        risk_data = calculate_product_risk(p['product_id'])
        risk_item = {
            "product_id": p['product_id'],
            "product_name": p['product_name'],
            "brand": p['brand'],
            "category": p['category'],
            "status": p['status'],
            "risk_score": risk_data['risk_score'],
            "risk_level": risk_data['risk_level'],
            "reason": risk_data['reason'],
            "total_attempts": risk_data['total_attempts'],
            "failed_attempts": risk_data['failed_attempts'],
            "distinct_devices": risk_data['distinct_devices'],
            "failure_rate": risk_data['failure_rate']
        }
        product_risks.append(risk_item)
        total_risk_score_sum += risk_data['risk_score']
        
        if risk_data['risk_level'] in ['HIGH', 'CRITICAL']:
            high_risk_products.append(risk_item)
        if risk_data['risk_level'] in ['MEDIUM', 'HIGH', 'CRITICAL'] or risk_data['failed_attempts'] > 0:
            suspicious_products.append(risk_item)

    avg_system_risk = round(total_risk_score_sum / len(products), 1) if products else 0.0

    # Process logs for Chart.js
    df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()
    
    daily_labels = []
    daily_counts = []
    success_count = 0
    failed_count = 0
    suspicious_count = 0
    
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for pr in product_risks:
        level = pr['risk_level']
        risk_distribution[level] = risk_distribution.get(level, 0) + 1

    if not df_logs.empty and 'timestamp' in df_logs.columns:
        success_count = len(df_logs[df_logs['verification_status'] == 'VERIFIED'])
        failed_count = len(df_logs[df_logs['verification_status'].isin(['INCORRECT_CODE', 'INVALID_REFERENCE'])])
        suspicious_count = len(df_logs[df_logs['verification_status'] == 'SUSPICIOUS'])
        
        # Daily counts for chart (past 7 days)
        df_logs['date'] = pd.to_datetime(df_logs['timestamp'], errors='coerce').dt.strftime('%b %d')
        daily_grp = df_logs.groupby('date').size().reset_index(name='count')
        daily_labels = daily_grp['date'].tolist()[-7:]
        daily_counts = daily_grp['count'].tolist()[-7:]
    else:
        # Fallback empty chart data
        daily_labels = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in reversed(range(7))]
        daily_counts = [0] * 7

    # Top verified products count
    top_products = sorted(product_risks, key=lambda x: x['total_attempts'], reverse=True)[:5]

    total_logs_count = len(logs)
    failed_rate = round((failed_count / total_logs_count * 100), 1) if total_logs_count > 0 else 0.0

    return {
        "overall_risk_score": avg_system_risk,
        "overall_risk_level": "CRITICAL" if avg_system_risk > 80 else ("HIGH" if avg_system_risk > 60 else ("MEDIUM" if avg_system_risk > 30 else "LOW")),
        "total_products_analyzed": len(products),
        "high_risk_count": len(high_risk_products),
        "suspicious_count": len(suspicious_products),
        "failed_verification_rate": failed_rate,
        "product_risks": sorted(product_risks, key=lambda x: x['risk_score'], reverse=True),
        "high_risk_products": high_risk_products,
        "suspicious_products": suspicious_products,
        "top_verified_products": top_products,
        "charts": {
            "daily_labels": daily_labels,
            "daily_counts": daily_counts,
            "verification_status": {
                "success": success_count,
                "failed": failed_count,
                "suspicious": suspicious_count
            },
            "risk_distribution": risk_distribution
        }
    }
