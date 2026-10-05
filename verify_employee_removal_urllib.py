import urllib.request
import urllib.parse
import http.cookiejar
import json

BASE_URL = "http://127.0.0.1:5000"

# Setup cookie jar for session management
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

def verify_employee_lifecycle():
    print("1. Logging in as Admin...")
    login_data = urllib.parse.urlencode({
        "username": "murugan", 
        "password": "murugan@123", 
        "role": "admin"
    }).encode()
    
    try:
        req = urllib.request.Request(f"{BASE_URL}/login", data=login_data)
        with opener.open(req) as response:
            if response.geturl() == f"{BASE_URL}/admin":
                print("   Success: Logged in.")
            else:
                print(f"   Failed: Login failed. Redirected to {response.geturl()}")
                return
    except Exception as e:
        print(f"   Failed: Login error {e}")
        return

    print("\n2. Creating Test Employee...")
    test_emp = {
        "username": "verify_test_user_urllib",
        "password": "password123",
        "place": "Test Hub"
    }
    json_data = json.dumps(test_emp).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/employee/create", data=json_data, headers={'Content-Type': 'application/json'})
    
    try:
        with opener.open(req) as response:
            if response.status == 201:
                print("   Success: Employee created.")
            else:
                print(f"   Failed: Status {response.status}")
    except urllib.error.HTTPError as e:
        print(f"   Failed: Create error {e.code} - {e.read()}")
        return

    print("\n3. Verifying Employee in Admin Page...")
    try:
        with opener.open(f"{BASE_URL}/admin") as response:
            content = response.read().decode('utf-8')
            if "verify_test_user_urllib" in content:
                print("   Success: Employee found in admin dashboard.")
            else:
                print("   Failed: Employee NOT found in admin dashboard.")
    except Exception as e:
        print(f"   Failed: Error fetching admin page {e}")

    print("\n4. Deleting Test Employee...")
    del_data = json.dumps({"username": "verify_test_user_urllib"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/employee/delete", data=del_data, headers={'Content-Type': 'application/json'})
    
    try:
        with opener.open(req) as response:
            if response.status == 200:
                print("   Success: Employee deleted.")
            else:
                print(f"   Failed: Delete status {response.status}")
    except urllib.error.HTTPError as e:
        print(f"   Failed: Delete error {e.code} - {e.read()}")

    print("\n5. Verifying Deletion...")
    try:
        with opener.open(f"{BASE_URL}/admin") as response:
            content = response.read().decode('utf-8')
            if "verify_test_user_urllib" not in content:
                print("   Success: Employee successfully removed from dashboard.")
            else:
                print("   Failed: Employee STILL present in admin dashboard.")
    except Exception as e:
        print(f"   Failed: Error fetching admin page {e}")

if __name__ == "__main__":
    verify_employee_lifecycle()
