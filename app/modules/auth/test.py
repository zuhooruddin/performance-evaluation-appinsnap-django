import sys
import os

# Ensure Python finds the 'app' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.auth.auth import AuthService, LoginRequest, OTPVerifyRequest, UserAccessCreate
from app.core.storage import Storage

def menu():
    print("\n" + "="*45)
    print("   SAAS IDENTITY & ACCESS MANAGEMENT")
    print("="*45)
    print("1. Register New Access Profile")
    print("2. Restrict / Unrestrict User Access")
    print("3. Login (Request OTP)")
    print("4. Confirm Login (Submit OTP)")
    print("5. View Registered Access Profiles")
    print("6. Exit")
    print("="*45)

def run():
    # Automatically setup the hardcoded admin on startup
    AuthService.bootstrap_admin()
    print("✅ System Auth initialized. Default Admin (ADM-01) is ready.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- REGISTER ACCESS PROFILE --")
                email = input("Email: ").strip()
                name = input("Full Name: ").strip()
                print("Available Roles: admin, evaluator, employee")
                role = input("System Role: ").strip().lower()
                
                title = None
                if role == "evaluator":
                    title = input("Job Title (e.g., CTO, HR, Line Manager): ").strip()
                
                perms_input = input("Permissions (comma separated, leave blank for default): ").strip()
                perms = [p.strip() for p in perms_input.split(",")] if perms_input else []
                
                user = AuthService.register_access_profile(UserAccessCreate(
                    email=email, 
                    name=name,
                    system_role=role, 
                    custom_title=title,
                    permissions=perms
                ))
                print(f"✅ Success! Profile created with ID: {user['id']}")

            elif choice == "2":
                print("\n-- TOGGLE RESTRICTION --")
                email = input("User Email: ").strip()
                action = input("Restrict this user? (y/n): ").strip().lower()
                restrict = True if action == 'y' else False
                
                res = AuthService.toggle_restriction(email, restrict)
                print(f"✅ {res['message']}")

            elif choice == "3":
                print("\n-- SYSTEM LOGIN --")
                email = input("Email: ").strip()
                role = input("Role (admin/evaluator/employee): ").strip()
                res = AuthService.request_login(LoginRequest(email=email, role=role))
                print(f"\n📩 {res['message']}!")
                print(f"🔒 YOUR OTP IS: {res['otp']}")

            elif choice == "4":
                print("\n-- CONFIRM LOGIN --")
                email = input("Email: ").strip()
                otp = input("Enter 6-digit OTP: ").strip()
                res = AuthService.verify_otp(OTPVerifyRequest(email=email, otp=otp))
                print(f"\n✅ {res['message']}!")
                print(f"🔑 Session Token: {res['token']}")

            elif choice == "5":
                print("\n[REGISTERED ACCESS PROFILES]")
                users = Storage.load("users")
                for u in users.values():
                    status = "🟢 Active" if u.get('is_active', True) else "🔴 Restricted"
                    title_display = f" | Title: {u.get('custom_title')}" if u.get('custom_title') else ""
                    print(f"[{u['id']}] {u['name']} ({u['email']}) | Role: {u['system_role']}{title_display} | {status}")

            elif choice == "6":
                print("Exiting simulator...")
                break

            else:
                print("❌ Invalid choice. Try again.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run()