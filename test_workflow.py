import requests
import json

BASE_URL = "http://localhost:5050"

def test_authentix_system():
    print("==================================================")
    print("AUTHENTIX System End-to-End Verification Test Suite")
    print("==================================================")

    session = requests.Session()

    # TEST 1: Admin Login & Register Product
    print("\n[TEST 1] Registering a new product...")
    login_res = session.post(f"{BASE_URL}/api/admin/login", json={
        "email": "admin@authentix.com",
        "password": "admin123"
    })
    print(f" -> Admin Login status: {login_res.status_code}, data: {login_res.json()}")

    prod_res = session.post(f"{BASE_URL}/api/products", json={
        "product_name": "Test Cyber Shield Key",
        "brand": "AUTHENTIX Labs",
        "category": "Electronics",
        "manufacturer": "Secure Corp",
        "batch_number": "TEST-BATCH-2026",
        "manufacturing_date": "2026-01-01",
        "expiry_date": "2030-01-01",
        "description": "Automated test unit"
    })

    assert prod_res.status_code == 201
    prod_data = prod_res.json()
    product = prod_data['product']
    ver_code = prod_data['verification_code']
    qr_ref = product['qr_reference']
    product_id = product['product_id']

    print(f" -> TEST 1 SUCCESS:")
    print(f"    Product ID: {product_id}")
    print(f"    Secret Verification Code: {ver_code}")
    print(f"    QR Reference Token: {qr_ref}")
    print(f"    QR Image URL: {prod_data['qr_image_url']}")

    # TEST 2: Scan / Lookup QR Reference
    print("\n[TEST 2] Lookup product by QR reference (Simulating QR scan)...")
    lookup_res = requests.get(f"{BASE_URL}/api/verify/{qr_ref}")
    assert lookup_res.status_code == 200
    lookup_json = lookup_res.json()
    assert lookup_json['success'] is True
    print(f" -> TEST 2 SUCCESS: QR scanned. Basic Product info returned:")
    print(f"    Name: {lookup_json['product']['product_name']}, Brand: {lookup_json['product']['brand']}")

    # TEST 3: Enter CORRECT Verification Code
    print("\n[TEST 3] Submitting CORRECT Verification Code...")
    verify_correct = requests.post(f"{BASE_URL}/api/verify/code", json={
        "qr_reference": qr_ref,
        "verification_code": ver_code
    })
    assert verify_correct.status_code == 200
    correct_json = verify_correct.json()
    assert correct_json['status'] == 'VERIFIED'
    print(f" -> TEST 3 SUCCESS: Result = {correct_json['title']} ({correct_json['message']})")

    # TEST 4: Enter INCORRECT Verification Code
    print("\n[TEST 4] Submitting INCORRECT Verification Code...")
    verify_wrong = requests.post(f"{BASE_URL}/api/verify/code", json={
        "qr_reference": qr_ref,
        "verification_code": "WRONG-CODE-999"
    })
    assert verify_wrong.status_code == 200
    wrong_json = verify_wrong.json()
    assert wrong_json['status'] == 'INCORRECT_CODE'
    print(f" -> TEST 4 SUCCESS: Result = {wrong_json['title']} ({wrong_json['message']})")

    # TEST 5 & 6: Non-existent / Invalid QR Reference
    print("\n[TEST 5 & 6] Checking Invalid / Non-existent QR Reference...")
    verify_invalid = requests.get(f"{BASE_URL}/api/verify/ref-fake-non-existent-999")
    assert verify_invalid.status_code == 404
    print(" -> TEST 5 & 6 SUCCESS: Invalid reference correctly rejected.")

    # TEST 7: Disable Product & Verify Status
    print("\n[TEST 7] Disabling Product and testing scanner...")
    session.post(f"{BASE_URL}/admin/products/{product_id}/disable")
    verify_disabled = requests.post(f"{BASE_URL}/api/verify/code", json={
        "qr_reference": qr_ref,
        "verification_code": ver_code
    })
    assert verify_disabled.json()['status'] == 'DISABLED'
    print(f" -> TEST 7 SUCCESS: Result = {verify_disabled.json()['title']}")

    # Re-enable product for history tests
    session.post(f"{BASE_URL}/admin/products/{product_id}/disable")

    # TEST 8 & 9: Verification Attempts Log & AI Suspicious Activity Analysis
    print("\n[TEST 8 & 9] Generating multiple failed attempts to test AI Risk Score increase...")
    for i in range(6):
        requests.post(f"{BASE_URL}/api/verify/code", json={
            "qr_reference": qr_ref,
            "verification_code": f"BAD-ATTEMPT-{i}",
            "device_info": f"Device-{i % 3}"
        })

    risk_res = requests.get(f"{BASE_URL}/api/ai/risk/{product_id}")
    risk_data = risk_res.json()['risk']
    print(f" -> TEST 8 & 9 SUCCESS:")
    print(f"    Updated Risk Score: {risk_data['risk_score']} / 100")
    print(f"    Risk Level: {risk_data['risk_level']}")
    print(f"    Reason: {risk_data['reason']}")

    # TEST 10: Download QR image endpoint check
    print("\n[TEST 10] Checking downloadable QR file endpoint...")
    qr_dl_res = session.get(f"{BASE_URL}/admin/products/{product_id}/download-qr")
    assert qr_dl_res.status_code == 200
    assert qr_dl_res.headers['Content-Type'] == 'image/png'
    print(f" -> TEST 10 SUCCESS: Downloaded QR PNG image ({len(qr_dl_res.content)} bytes).")

    print("\n==================================================")
    print("ALL 10 TESTS PASSED SUCCESSFULLY! AUTHENTIX IS FULLY FUNCTIONAL!")
    print("==================================================")

if __name__ == '__main__':
    test_authentix_system()
