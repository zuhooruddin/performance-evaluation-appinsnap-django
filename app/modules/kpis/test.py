import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.kpis.kpis import KPIService, KPICreate, KPIUpdate
from app.modules.teams.teams import TeamService

def menu():
    print("\n" + "="*45)
    print("   TEAM KPIs (Performance Metrics)")
    print("="*45)
    print("1. Create New KPI for a Team")
    print("2. List Active KPIs (By Team or All)")
    print("3. Update a KPI")
    print("4. Archive a KPI")
    print("5. Exit")
    print("="*45)

def show_teams():
    print("\n--- Available Active Teams ---")
    teams = TeamService.list_all(include_archived=False)
    if not teams:
        print("⚠️ No active teams. Create one first!")
        return False
    for t in teams:
        print(f"[{t['id']}] {t['name']} (Dept: {t['department_id']})")
    print("------------------------------")
    return True

def run():
    print("✅ KPI testing module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- CREATE KPI --")
                if not show_teams(): continue
                
                team_id = input("Enter Target Team ID (e.g., TM-01): ").strip()
                title = input("KPI Title (e.g., Code Quality): ").strip()
                desc = input("Description: ").strip()
                weight = float(input("Weight (0.01 to 1.00, e.g., 0.5 for 50%): ").strip())
                
                kpi = KPIService.create(KPICreate(
                    team_id=team_id,
                    title=title,
                    description=desc,
                    weight=weight
                ))
                print(f"✅ Success! Created KPI [{kpi['id']}] - {kpi['title']}")

            elif choice == "2":
                print("\n-- LIST KPIs --")
                filter_team = input("Filter by Team ID? (Leave blank for all): ").strip()
                team_id = filter_team if filter_team else None
                
                kpis = KPIService.list_all(team_id=team_id, include_archived=False)
                if not kpis:
                    print("⚠️ No active KPIs found.")
                    
                for k in kpis:
                    weight_pct = int(k['weight'] * 100)
                    print(f"🎯 [{k['id']}] {k['title']} | Team: {k['team_id']} | Weight: {weight_pct}%")

            elif choice == "3":
                print("\n-- UPDATE KPI --")
                kpi_id = input("Enter KPI ID (e.g., KPI-01): ").strip()
                title = input("New Title (leave blank to skip): ").strip()
                desc = input("New Description (leave blank to skip): ").strip()
                weight_str = input("New Weight (leave blank to skip): ").strip()
                
                payload = {}
                if title: payload["title"] = title
                if desc: payload["description"] = desc
                if weight_str: payload["weight"] = float(weight_str)
                
                res = KPIService.update(kpi_id, KPIUpdate(**payload))
                print(f"✅ Successfully updated [{res['id']}] {res['title']}")

            elif choice == "4":
                print("\n-- ARCHIVE KPI --")
                kpi_id = input("Enter KPI ID to archive: ").strip()
                res = KPIService.archive(kpi_id)
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