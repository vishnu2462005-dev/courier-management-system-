import requests

BASE_URL = "http://127.0.0.1:5000"
ADMIN_CREDS = {"username": "murugan", "password": "murugan@123", "role": "admin"}

session = requests.Session()

def verify_employee_lifecycle():
    print("1. Logging in as Admin...")
    login_resp = session.post(f"{BASE_URL}/login", data=ADMIN_CREDS)
    if login_resp.url == f"{BASE_URL}/admin":
        print("   Success: Logged in.")
    else:
        print(f"   Failed: Login failed. Redirected to {login_resp.url}")
        return

    print("\n2. Creating Test Employee...")
    test_emp = {
        "username": "verify_test_user",
        "password": "password123",
        "place": "Test Hub"
    }
    create_resp = session.post(f"{BASE_URL}/api/employee/create", json=test_emp)
    if create_resp.status_code == 201:
        print("   Success: Employee created.")
    else:
        print(f"   Failed: {create_resp.text}")

    print("\n3. Verifying Employee in Admin Page (Response Content)...")
    # Since we can't parse HTML easily without bs4 (and I don't want to install it if not there), 
    # I'll checking string presence in response.
    admin_page = session.get(f"{BASE_URL}/admin")
    if "verify_test_user" in admin_page.text:
       print("   Success: Employee found in admin dashboard.")
    else:
       print("   Failed: Employee NOT found in admin dashboard.")

    print("\n4. Deleting Test Employee...")
    del_resp = session.post(f"{BASE_URL}/api/employee/delete", json={"username": "verify_test_user"})
    if del_resp.status_code == 200:
        print("   Success: Employee deleted.")
    else:
        print(f"   Failed: Delete failed. {del_resp.text}")

    print("\n5. Verifying Deletion...")
    admin_page_after = session.get(f"{BASE_URL}/admin")
    if "verify_test_user" not in admin_page_after.text:
       print("   Success: Employee successfully removed from dashboard.")
    else:
       print("   Failed: Employee STILL present in admin dashboard.")

if __name__ == "__main__":
    try:
        verify_employee_lifecycle()
    except Exception as e:
        print(f"An error occurred: {e}")
