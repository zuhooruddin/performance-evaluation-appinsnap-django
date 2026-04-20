import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.teams.teams import TeamService, TeamCreate, TeamUpdate
from app.modules.departments.departments import DepartmentService

def menu():
    print("\n" + "="*45)
    print("   TEAMS MANAGEMENT (SaaS Core)")
    print("="*45)
    print("1. Create a New Team")
    print("2. List Active Teams (All or By Dept)")
    print("3. List ALL Teams (Includes Archived)")
    print("4. Update / Restore Team")
    print("5. Archive Team (Soft Delete)")
    print("6. Exit")
    print("="*45)

def show_departments():
    print("\n--- Available Departments ---")
    depts = DepartmentService.list_all(include_archived=False)
    if not depts:
        print("⚠️ No active departments. Create one first!")
        return False
    for d in depts:
        print(f"[{d['id']}] {d['name']}")
    print("-----------------------------")
    return True

def run():
    print("✅ Teams testing module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- CREATE TEAM --")
                if not show_departments(): continue
                
                dept_id = input("Enter Department ID (e.g., DPT-01): ").strip()
                name = input("Team Name (e.g., Backend Dev): ").strip()
                desc = input("Description (optional): ").strip()
                
                team = TeamService.create(TeamCreate(
                    name=name, 
                    department_id=dept_id,
                    description=desc if desc else None
                ))
                print(f"✅ Success! Created [{team['id']}] - {team['name']}")

            elif choice == "2":
                print("\n-- LIST TEAMS --")
                filter_dept = input("Filter by Dept ID? (Leave blank for all): ").strip()
                dept_id = filter_dept if filter_dept else None
                
                teams = TeamService.list_all(department_id=dept_id, include_archived=False)
                if not teams:
                    print("⚠️ No active teams found.")
                for t in teams:
                    lead = t.get('team_lead_id') or "Unassigned"
                    print(f"👥 [{t['id']}] {t['name']} (Dept: {t['department_id']}) | Lead: {lead}")

            elif choice == "3":
                print("\n[ALL TEAMS]")
                teams = TeamService.list_all(include_archived=True)
                for t in teams:
                    status = "🟢 Active" if t.get('is_active', True) else "🔴 Archived"
                    print(f"👥 [{t['id']}] {t['name']} (Dept: {t['department_id']}) | Status: {status}")

            elif choice == "4":
                print("\n-- UPDATE TEAM --")
                team_id = input("Enter Team ID (e.g., TM-01): ").strip()
                name = input("New Name (leave blank to skip): ").strip()
                desc = input("New Description (leave blank to skip): ").strip()
                is_active_str = input("Restore if archived? (y/n, blank to skip): ").strip().lower()
                
                payload = {}
                if name: payload["name"] = name
                if desc: payload["description"] = desc
                if is_active_str == 'y': payload["is_active"] = True
                
                res = TeamService.update(team_id, TeamUpdate(**payload))
                print(f"✅ Successfully updated [{res['id']}] {res['name']}")

            elif choice == "5":
                print("\n-- ARCHIVE TEAM --")
                team_id = input("Enter Team ID to archive: ").strip()
                res = TeamService.archive(team_id)
                print(f"✅ {res['message']}")

            elif choice == "6":
                print("Exiting simulator...")
                break
            
            else:
                print("❌ Invalid choice.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run()