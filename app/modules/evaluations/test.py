import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.modules.evaluations.evaluations import EvaluationService, EvaluationCreate, KPIScoreInput
from app.modules.evaluators.evaluators import EvaluatorService
from app.core.storage import Storage

def menu():
    print("\n" + "="*50)
    print("   SCORING ENGINE (Final Evaluations)")
    print("="*50)
    print("1. Submit an Evaluation (Grade an Employee)")
    print("2. View Final Results for an Employee")
    print("3. Exit")
    print("="*50)

def run():
    print("✅ Evaluation Scoring Engine initialized.")

    while True:
        menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                print("\n-- SUBMIT EVALUATION --")
                evaluator_id = input("Enter YOUR HR Profile ID (Who are you? e.g., HR-01): ").strip()
                
                # Fetch pending assignments for this evaluator
                asns = EvaluatorService.list_all(evaluator_id=evaluator_id)
                pending = []
                evals = Storage.load("evaluations")
                
                for a in asns:
                    # Check if already submitted
                    if not any(e["assignment_id"] == a["id"] for e in evals.values()):
                        pending.append(a)

                if not pending:
                    print("⚠️ You have no pending evaluations to submit.")
                    continue
                
                print("\nYour Pending Assignments:")
                for p in pending:
                    print(f"[{p['id']}] Grade: {p['evaluatee_id']} | Cycle: {p['cycle_id']} | Max Points: {p['weight']}")
                
                asn_id = input("\nEnter the Assignment ID you want to complete: ").strip()
                selected_asn = next((p for p in pending if p['id'] == asn_id), None)
                
                if not selected_asn:
                    print("❌ Invalid Assignment ID.")
                    continue

                # Fetch KPIs for the Evaluatee's Team
                employees = Storage.load("employees")
                evaluatee_team = employees[selected_asn["evaluatee_id"]]["team_id"]
                all_kpis = Storage.load("kpis")
                team_kpis = [k for k in all_kpis.values() if k["team_id"] == evaluatee_team and k.get("is_active", True)]
                
                if not team_kpis:
                    print(f"❌ Cannot evaluate: Team {evaluatee_team} has no active KPIs.")
                    continue
                
                print(f"\n--- Grading {selected_asn['evaluatee_id']} on {len(team_kpis)} KPIs ---")
                print("Enter a score from 0 to 100 for each metric.")
                
                scores = []
                for kpi in team_kpis:
                    score_val = float(input(f"> Score for '{kpi['title']}': ").strip())
                    scores.append(KPIScoreInput(kpi_id=kpi["id"], score=score_val))
                    
                comments = input("\nAny final comments? (Optional): ").strip()

                result = EvaluationService.create(EvaluationCreate(
                    assignment_id=asn_id,
                    kpi_scores=scores,
                    comments=comments if comments else None
                ))
                
                print(f"\n✅ EVALUATION SUBMITTED SUCCESSFULLY! [{result['id']}]")
                print(f"🏆 Final Points Awarded: {result['total_points_earned']} / {result['max_points_possible']}")

            elif choice == "2":
                print("\n-- VIEW RESULTS --")
                evaluatee_id = input("Enter Evaluatee HR-ID (e.g., HR-02): ").strip()
                cycle_id = input("Enter Cycle ID (e.g., CYC-01): ").strip()
                
                evals = EvaluationService.list_all(cycle_id=cycle_id, evaluatee_id=evaluatee_id)
                if not evals:
                    print("⚠️ No evaluations submitted for this user in this cycle yet.")
                
                total_earned = 0.0
                total_possible = 0.0
                
                for e in evals:
                    print(f"\n--- Evaluation by {e['evaluator_id']} ---")
                    print(f"Points Awarded: {e['total_points_earned']} / {e['max_points_possible']}")
                    if e['comments']:
                        print(f"Comments: \"{e['comments']}\"")
                    
                    total_earned += e['total_points_earned']
                    total_possible += e['max_points_possible']
                    
                if evals:
                    print("\n" + "="*40)
                    print(f"🌟 OVERALL CYCLE SCORE: {round(total_earned, 2)} / {total_possible}")
                    print("="*40)

            elif choice == "3":
                print("Exiting simulator...")
                break
            
            else:
                print("❌ Invalid choice.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run()