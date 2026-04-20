import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.evaluators.evaluators import EvaluatorService, AssignmentCreate
from app.modules.cycles.cycles import CycleService
from app.modules.employees.employees import EmployeeService

def menu():
    print("\n" + "="*50)
    print("   EVALUATOR ASSIGNMENTS (The Scoring Engine)")
    print("="*50)
    print("1. Create New Assignment (Assign Evaluator)")
    print("2. View a User's Evaluators")
    print("3. View Who a User is Evaluating")
    print("4. Remove Assignment")
    print("5. Exit")
    print("="*50)

def show_context():
    print("\n--- Available Active Cycles ---")
    cycles = CycleService.list_all()
    for c in cycles:
        if c['status'] != 'completed':
            print(f"[{c['id']}] {c['name']} (Status: {c['status']})")
            
    print("\n--- Available HR Profiles ---")
    emps = EmployeeService.list_all(include_archived=False)
    for e in emps:
        print(f"[{e['id']}] {e['email']} (Team: {e['team_id']})")
    print("-------------------------------")

def run():
    print("✅ Evaluator Assignment module initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                show_context()
                print("\n-- CREATE ASSIGNMENT --")
                cycle_id = input("Cycle ID (e.g., CYC-01): ").strip()
                evaluatee_id = input("Evaluatee ID (Who is being graded? HR-xx): ").strip()
                evaluator_id = input("Evaluator ID (Who is doing the grading? HR-yy): ").strip()
                role = input("Evaluator Role (e.g., Line Manager, HR, Peer): ").strip()
                weight = float(input("Weight / Max Points (e.g., 20): ").strip())
                
                asn = EvaluatorService.create(AssignmentCreate(
                    cycle_id=cycle_id,
                    evaluatee_id=evaluatee_id,
                    evaluator_id=evaluator_id,
                    evaluator_role=role,
                    weight=weight
                ))
                print(f"✅ Success! Assignment [{asn['id']}] created.")

            elif choice == "2":
                print("\n-- WHO IS GRADING THIS USER? --")
                eval_id = input("Enter Evaluatee HR-ID: ").strip()
                asns = EvaluatorService.list_all(evaluatee_id=eval_id)
                if not asns:
                    print("⚠️ No evaluators assigned to this user.")
                
                total_weight = 0
                for a in asns:
                    total_weight += a['weight']
                    print(f"[{a['id']}] Evaluator: {a['evaluator_id']} | Role: {a['evaluator_role']} | Weight: {a['weight']}")
                print(f"-> Total Evaluation Weight Available: {total_weight} points")

            elif choice == "3":
                print("\n-- WHO IS THIS USER GRADING? --")
                eval_id = input("Enter Evaluator HR-ID: ").strip()
                asns = EvaluatorService.list_all(evaluator_id=eval_id)
                if not asns:
                    print("⚠️ This user is not assigned to evaluate anyone.")
                for a in asns:
                    print(f"[{a['id']}] Evaluating: {a['evaluatee_id']} | Cycle: {a['cycle_id']} | As: {a['evaluator_role']}")

            elif choice == "4":
                print("\n-- REMOVE ASSIGNMENT --")
                asn_id = input("Enter Assignment ID (ASN-xx): ").strip()
                res = EvaluatorService.remove(asn_id)
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