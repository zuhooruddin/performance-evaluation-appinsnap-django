import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.cycles.cycles import CycleService, CycleCreate, CycleUpdate, CycleStatus

def menu():
    print("\n" + "="*45)
    print("   EVALUATION CYCLES (SaaS Core)")
    print("="*45)
    print("1. Create New Cycle (Draft)")
    print("2. List All Cycles")
    print("3. Activate a Cycle")
    print("4. Mark Cycle as Completed")
    print("5. Exit")
    print("="*45)

def run():
    print("✅ Evaluation Cycles testing module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- CREATE NEW CYCLE --")
                name = input("Cycle Name (e.g., Q1 2026 Performance): ").strip()
                start = input("Start Date (YYYY-MM-DD): ").strip()
                end = input("End Date (YYYY-MM-DD): ").strip()
                
                cyc = CycleService.create(CycleCreate(name=name, start_date=start, end_date=end))
                print(f"✅ Success! Created Cycle [{cyc['id']}] as DRAFT.")

            elif choice == "2":
                print("\n-- SYSTEM CYCLES --")
                cycles = CycleService.list_all()
                if not cycles:
                    print("⚠️ No cycles found.")
                for c in cycles:
                    status_emoji = "⚪" if c['status'] == 'draft' else "🟢" if c['status'] == 'active' else "🔴"
                    print(f"{status_emoji} [{c['id']}] {c['name']} | {c['start_date']} to {c['end_date']} | Status: {c['status'].upper()}")

            elif choice == "3":
                print("\n-- ACTIVATE CYCLE --")
                cyc_id = input("Enter Cycle ID (e.g., CYC-01): ").strip()
                res = CycleService.update(cyc_id, CycleUpdate(status=CycleStatus.ACTIVE))
                print(f"✅ Cycle {res['id']} is now ACTIVE! Employees can now be evaluated.")

            elif choice == "4":
                print("\n-- COMPLETE CYCLE --")
                cyc_id = input("Enter Cycle ID to complete: ").strip()
                confirm = input("Are you sure? This locks the cycle permanently. (y/n): ").strip().lower()
                if confirm == 'y':
                    res = CycleService.update(cyc_id, CycleUpdate(status=CycleStatus.COMPLETED))
                    print(f"✅ Cycle {res['id']} is officially CLOSED and COMPLETED.")

            elif choice == "5":
                print("Exiting simulator...")
                break
            
            else:
                print("❌ Invalid choice.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run()