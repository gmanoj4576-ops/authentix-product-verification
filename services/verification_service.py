from datetime import datetime, timedelta
import database.db as db
from services.qr_service import verify_code_hash
from ml.anomaly_detector import calculate_product_risk

def process_verification(qr_reference, submitted_code, device_info="Browser Camera Scanner", source="web_camera"):
    """
    Core verification pipeline:
    1. QR Reference lookup
    2. Check Product Status (Active, Disabled, Expired)
    3. Verification Code hash comparison
    4. Rate limit / Anomaly detection check
    5. Log verification attempt
    6. Return standard structured result
    """
    # 1. Lookup QR Reference
    product = db.get_product_by_ref(qr_reference)
    
    if not product:
        # Record failed attempt for invalid reference
        db.log_verification(
            product_id=None,
            status="INVALID_REFERENCE",
            failure_reason="QR Reference not found in database",
            device_info=device_info,
            source=source,
            risk_score=90.0
        )
        return {
            "status": "INVALID_REFERENCE",
            "success": False,
            "title": "INVALID PRODUCT",
            "message": "This product reference could not be found in the verification system.",
            "product": None
        }

    product_id = product['product_id']
    product_status = product.get('status', 'Active')
    
    # 2. Check Product Status
    if product_status == 'Disabled':
        db.log_verification(
            product_id=product_id,
            status="DISABLED",
            failure_reason="Product marked as disabled by manufacturer",
            device_info=device_info,
            source=source,
            risk_score=50.0
        )
        return {
            "status": "DISABLED",
            "success": False,
            "title": "PRODUCT VERIFICATION UNAVAILABLE",
            "message": "This product registration has been disabled or suspended by the manufacturer.",
            "product": product
        }
        
    if product_status == 'Expired':
        db.log_verification(
            product_id=product_id,
            status="EXPIRED",
            failure_reason="Product has passed its expiration date",
            device_info=device_info,
            source=source,
            risk_score=40.0
        )
        return {
            "status": "EXPIRED",
            "success": False,
            "title": "PRODUCT EXPIRED",
            "message": "This product has passed its authorized expiration date.",
            "product": product
        }

    # 3. Rate limiting & Suspicious Activity Detection before code check
    recent_logs = db.get_verification_logs(product_id=product_id, limit=20)
    failed_recent = sum(1 for log in recent_logs[:5] if log['verification_status'] in ('INCORRECT_CODE', 'SUSPICIOUS'))
    
    is_suspicious_spike = failed_recent >= 4

    # 4. Verification Code Check
    stored_hash = product.get('verification_code_hash')
    is_code_correct = verify_code_hash(submitted_code, stored_hash)

    # 5. Calculate AI Risk Score after attempt
    risk_analysis = calculate_product_risk(product_id)
    current_risk_score = risk_analysis.get('risk_score', 0.0)

    if is_code_correct:
        status = "VERIFIED"
        if is_suspicious_spike:
            status = "SUSPICIOUS" # Code correct, but flagged due to extreme high rate
        
        db.log_verification(
            product_id=product_id,
            status=status,
            failure_reason="" if status == "VERIFIED" else "High failed attempts frequency prior to success",
            device_info=device_info,
            source=source,
            risk_score=current_risk_score
        )
        
        # Save updated risk evaluation
        db.save_risk_analysis(
            product_id=product_id,
            risk_score=risk_analysis['risk_score'],
            risk_level=risk_analysis['risk_level'],
            reason=risk_analysis['reason'],
            model_version=risk_analysis['model_version']
        )
        
        return {
            "status": "VERIFIED",
            "success": True,
            "title": "GENUINE PRODUCT",
            "message": "This product has been successfully verified.",
            "verification_time": datetime.now().strftime("%B %d, %Y - %H:%M:%S UTC"),
            "product": {
                "product_id": product['product_id'],
                "product_name": product['product_name'],
                "brand": product['brand'],
                "category": product['category'],
                "manufacturer": product.get('manufacturer', 'N/A'),
                "batch_number": product['batch_number'],
                "manufacturing_date": product.get('manufacturing_date', 'N/A'),
                "expiry_date": product.get('expiry_date', 'N/A'),
                "description": product.get('description', ''),
                "image_url": product.get('image_url', '')
            },
            "risk": risk_analysis
        }
    else:
        # Incorrect Verification Code
        db.log_verification(
            product_id=product_id,
            status="INCORRECT_CODE",
            failure_reason="Submitted verification code did not match product records",
            device_info=device_info,
            source=source,
            risk_score=current_risk_score + 15.0
        )
        
        # Re-evaluate risk score after failure
        updated_risk = calculate_product_risk(product_id)
        db.save_risk_analysis(
            product_id=product_id,
            risk_score=updated_risk['risk_score'],
            risk_level=updated_risk['risk_level'],
            reason=updated_risk['reason'],
            model_version=updated_risk['model_version']
        )
        
        return {
            "status": "INCORRECT_CODE",
            "success": False,
            "title": "POSSIBLE COUNTERFEIT",
            "message": "The verification code does not match our product records. Please check the product carefully.",
            "product": {
                "product_id": product['product_id'],
                "product_name": product['product_name'],
                "brand": product['brand']
            },
            "risk": updated_risk
        }
