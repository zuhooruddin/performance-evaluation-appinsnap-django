import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.employees.employees import EmployeeService, EmployeeCreate, EmployeeUpdate
from app.modules.teams.teams import TeamService
from app.modules.auth.auth import AuthService

def menu():
    print("\n" + "="*45)
    print("   EMPLOYEE HR PROFILES (SaaS Core)")
    print("="*45)
    print("1. Assign User to a Team (Create HR Profile)")
    print("2. List Active HR Profiles")
    print("3. Transfer Employee to New Team")
    print("4. Archive HR Profile (Soft Delete)")
    print("5. Exit")
    print("="*45)

def show_available_data():
    print("\n--- Available Users in Auth ---")
    users = AuthService.list_users()
    for u in users.values():
        if u.get("is_active", True):
            print(f"- {u['name']} ({u['email']}) | Role: {u['system_role']}")
            
    print("\n--- Available Teams ---")
    teams = TeamService.list_all(include_archived=False)
    for t in teams:
        print(f"[{t['id']}] {t['name']}")
    print("-------------------------------")

def run():
    print("✅ Employee HR testing module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- CREATE HR PROFILE --")
                show_available_data()
                
                email = input("\nEnter User's Email: ").strip()
                team_id = input("Enter Target Team ID (e.g., TM-01): ").strip()
                
                emp = EmployeeService.create(EmployeeCreate(email=email, team_id=team_id))
                print(f"✅ Success! Created HR Profile [{emp['id']}] for {emp['email']} in {emp['department_id']}/{emp['team_id']}")

            elif choice == "2":
                print("\n-- LIST HR PROFILES --")
                filter_team = input("Filter by Team ID? (Leave blank for all): ").strip()
                
                emps = EmployeeService.list_all(team_id=filter_team if filter_team else None)
                if not emps:
                    print("⚠️ No active HR profiles found.")
                for e in emps:
                    print(f"👤 [{e['id']}] {e['email']} | Dept: {e['department_id']} | Team: {e['team_id']}")

            elif choice == "3":
                print("\n-- TRANSFER EMPLOYEE --")
                emp_id = input("Enter HR Profile ID (e.g., HR-01): ").strip()
                new_team = input("Enter NEW Team ID (e.g., TM-02): ").strip()
                
                res = EmployeeService.update(emp_id, EmployeeUpdate(team_id=new_team))
                print(f"✅ Transferred! Now in Dept: {res['department_id']} / Team: {res['team_id']}")

            elif choice == "4":
                print("\n-- ARCHIVE HR PROFILE --")
                emp_id = input("Enter HR Profile ID to archive: ").strip()
                res = EmployeeService.archive(emp_id)
                print(f"✅ {res['message']}")

            elif choice == "5":
                print("Exiting simulator...")
                break
            
            else:
                print("❌ Invalid choice.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run() 