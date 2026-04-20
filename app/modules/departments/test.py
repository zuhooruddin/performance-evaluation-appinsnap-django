import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.departments.departments import DepartmentService, DepartmentCreate, DepartmentUpdate

def menu():
    print("\n" + "="*45)
    print("   DEPARTMENTS MANAGEMENT (SaaS Core)")
    print("="*45)
    print("1. Create a New Department")
    print("2. List Active Departments")
    print("3. List ALL Departments (Includes Archived)")
    print("4. Update / Restore Department")
    print("5. Archive Department (Soft Delete)")
    print("6. Exit")
    print("="*45)

def run():
    print("✅ Department testing module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- CREATE DEPARTMENT --")
                name = input("Department Name (e.g., Engineering): ").strip()
                desc = input("Description (optional): ").strip()
                
                dept = DepartmentService.create(DepartmentCreate(
                    name=name, 
                    description=desc if desc else None
                ))
                print(f"✅ Success! Created [{dept['id']}] - {dept['name']}")

            elif choice == "2":
                print("\n[ACTIVE DEPARTMENTS]")
                depts = DepartmentService.list_all(include_archived=False)
                if not depts:
                    print("⚠️ No active departments found.")
                for d in depts:
                    head = d.get('head_id') or "Unassigned"
                    print(f"🏢 [{d['id']}] {d['name']} | Head: {head}")

            elif choice == "3":
                print("\n[ALL DEPARTMENTS]")
                depts = DepartmentService.list_all(include_archived=True)
                for d in depts:
                    status = "🟢 Active" if d['is_active'] else "🔴 Archived"
                    print(f"🏢 [{d['id']}] {d['name']} | Status: {status}")

            elif choice == "4":
                print("\n-- UPDATE DEPARTMENT --")
                dept_id = input("Enter Department ID (e.g., DPT-01): ").strip()
                name = input("New Name (leave blank to skip): ").strip()
                desc = input("New Description (leave blank to skip): ").strip()
                is_active_str = input("Restore if archived? (y/n, blank to skip): ").strip().lower()
                
                payload = {}
                if name: payload["name"] = name
                if desc: payload["description"] = desc
                if is_active_str == 'y': payload["is_active"] = True
                
                res = DepartmentService.update(dept_id, DepartmentUpdate(**payload))
                print(f"✅ Successfully updated [{res['id']}] {res['name']}")

            elif choice == "5":
                print("\n-- ARCHIVE DEPARTMENT --")
                dept_id = input("Enter Department ID to archive: ").strip()
                res = DepartmentService.archive(dept_id)
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