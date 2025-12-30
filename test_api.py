import requests
import json
from datetime import datetime

BASE = "http://127.0.0.1:8000"
OUTPUT_FILE = "record.json"

results = []


def pretty(o):
    return json.dumps(o, indent=2)


def save_results():
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to {OUTPUT_FILE}")


def run(name, method, url, body=None, expect=None):
    record = {
        "test_name": name,
        "method": method,
        "url": url,
        "request_body": body,
        "expected_status": expect,
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n=== {name} ===")
    try:
        if method == "GET":
            r = requests.get(url)
        elif method == "POST":
            r = requests.post(url, json=body)
        elif method == "PATCH":
            r = requests.patch(url, json=body)
        else:
            raise ValueError("Unsupported method")

        status = r.status_code
        record["actual_status"] = status
        record["response_text"] = r.text

        try:
            record["response_json"] = r.json()
        except:
            record["response_json"] = None

        ok = (expect is None) or (status == expect)
        record["result"] = "PASS" if ok else "FAIL"

        print(f"URL     : {url}")
        print(f"METHOD  : {method}")
        print(f"STATUS  : {status}  [{'PASS' if ok else 'FAIL'}]")
        print("RESPONSE:")
        try:
            print(pretty(r.json()))
        except:
            print(r.text)

    except Exception as e:
        print(f"ERROR calling API: {e}")
        record["result"] = "ERROR"
        record["error_message"] = str(e)

    results.append(record)

positive_tests = [
    # (test_name, method, endpoint, body, expected_status)
    ("POS01 Get Inventory", "GET", f"{BASE}/inventory", None, 200),
    ("POS02 Update Stock Valid", "PATCH", f"{BASE}/inventory/FUR001", {"stock": 20}, 200),
    ("POS03 Place Order Single Item", "POST", f"{BASE}/orders", {
        "customer_name": "Rahul",
        "items": [{"sku": "FUR001", "qty": 1}]
    }, 200),
    ("POS04 Place Order Multiple Items", "POST", f"{BASE}/orders", {
        "customer_name": "Amit",
        "items": [{"sku": "FUR002", "qty": 2}, {"sku": "FUR003", "qty": 1}]
    }, 200),
    ("POS05 Place Order Max Qty", "POST", f"{BASE}/orders", {
        "customer_name": "Riya",
        "items": [{"sku": "FUR004", "qty": 1}]
    }, 200),
    ("POS06 Get Order Detail", "GET", f"{BASE}/orders/1", None, 200),
    ("POS07 Update Stock to 0", "PATCH", f"{BASE}/inventory/FUR005", {"stock": 0}, 200),
    ("POS08 Reduce Stock", "PATCH", f"{BASE}/inventory/FUR006", {"stock": 5}, 200),
    ("POS09 Place Order Exact Stock", "POST", f"{BASE}/orders", {
        "customer_name": "Kunal",
        "items": [{"sku": "FUR006", "qty": 1}]
    }, 200),
    ("POS10 Place Order Different SKUs", "POST", f"{BASE}/orders", {
        "customer_name": "Meena",
        "items": [{"sku": "FUR007", "qty": 2}, {"sku": "FUR008", "qty": 1}]
    }, 200),
    ("POS11 Get Health", "GET", f"{BASE}/health", None, 200),
    ("POS12 Root Endpoint", "GET", f"{BASE}/", None, 200),
    ("POS13 Update Stock Large Value", "PATCH", f"{BASE}/inventory/FUR009", {"stock": 99}, 200),
    ("POS14 Place Order Big Quantity", "POST", f"{BASE}/orders", {
        "customer_name": "Dev",
        "items": [{"sku": "FUR009", "qty": 3}]
    }, 200),
    ("POS15 Order Lowercase SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Smriti",
        "items": [{"sku": "fur010", "qty": 1}]
    }, 200),
    ("POS16 Update Stock Again", "PATCH", f"{BASE}/inventory/FUR011", {"stock": 10}, 200),
    ("POS17 Order Recently Updated SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Vikas",
        "items": [{"sku": "FUR011", "qty": 1}]
    }, 200),
    ("POS18 Order Only 1 Item", "POST", f"{BASE}/orders", {
        "customer_name": "Shreya",
        "items": [{"sku": "FUR012", "qty": 1}]
    }, 200),
    ("POS19 Order Another Valid SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Arjun",
        "items": [{"sku": "FUR013", "qty": 2}]
    }, 200),
    ("POS20 Get Existing Order", "GET", f"{BASE}/orders/2", None, 200),
]

# ===========================
# NEGATIVE TEST CASES
# ===========================
negative_tests = [
    # (test_name, method, endpoint, body, expected_status)
    ("NEG01 Invalid SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Sam",
        "items": [{"sku": "BADSKU", "qty": 1}]
    }, 400),
    ("NEG02 Out of Stock", "POST", f"{BASE}/orders", {
        "customer_name": "John",
        "items": [{"sku": "FUR001", "qty": 99999}]
    }, 400),
    ("NEG03 Duplicate SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Ana",
        "items": [{"sku": "FUR002", "qty": 1}, {"sku": "FUR002", "qty": 1}]
    }, 400),
    ("NEG04 Negative Stock", "PATCH", f"{BASE}/inventory/FUR001", {"stock": -5}, 422),
    ("NEG05 Order Not Found", "GET", f"{BASE}/orders/99999", None, 404),
    ("NEG06 Missing Customer Name", "POST", f"{BASE}/orders", {
        "items": [{"sku": "FUR003", "qty": 1}]
    }, 422),
    ("NEG07 Negative Qty", "POST", f"{BASE}/orders", {
        "customer_name": "Bad",
        "items": [{"sku": "FUR003", "qty": -1}]
    }, 422),
    ("NEG08 Zero Qty", "POST", f"{BASE}/orders", {
        "customer_name": "Zero",
        "items": [{"sku": "FUR003", "qty": 0}]
    }, 422),
    ("NEG09 Update Stock Negative", "PATCH", f"{BASE}/inventory/FUR004", {"stock": -5}, 422),
    ("NEG10 Update Invalid SKU", "PATCH", f"{BASE}/inventory/WRONGSKU", {"stock": 5}, 404),
    ("NEG11 Invalid Body for Stock", "PATCH", f"{BASE}/inventory/FUR005", {"wrong": 5}, 422),
    ("NEG12 Stock Update No Body", "PATCH", f"{BASE}/inventory/FUR006", None, 422),
    ("NEG13 Invalid JSON", "POST", f"{BASE}/orders", "{bad json}", 400),
    ("NEG14 Missing Items Key", "POST", f"{BASE}/orders", {"customer_name": "Test"}, 422),
    ("NEG15 Empty SKU", "POST", f"{BASE}/orders", {
        "customer_name": "Bad",
        "items": [{"sku": "", "qty": 1}]
    }, 422),
    ("NEG16 Qty as String", "POST", f"{BASE}/orders", {
        "customer_name": "Bad",
        "items": [{"sku": "FUR007", "qty": "abc"}]
    }, 422),
    ("NEG17 Missing SKU Field", "POST", f"{BASE}/orders", {
        "customer_name": "Bad",
        "items": [{"qty": 2}]
    }, 422),
    ("NEG18 Fetch Order String ID", "GET", f"{BASE}/orders/abc", None, 422),
    ("NEG19 PATCH No Content-Type", "PATCH", f"{BASE}/inventory/FUR010", {"stock": 2}, 415),
    ("NEG20 POST No Content-Type", "POST", f"{BASE}/orders", {
        "customer_name": "Bad",
        "items": [{"sku": "FUR003", "qty": 1}]
    }, 415),]


def main():
    print("\n===== RUNNING POSITIVE TESTS =====")
    for name, m, u, b, e in positive_tests:
        run(name, m, u, b, e)

    print("\n===== RUNNING NEGATIVE TESTS =====")
    for name, m, u, b, e in negative_tests:
        run(name, m, u, b, e)

    save_results()


if __name__ == "__main__":
    main()