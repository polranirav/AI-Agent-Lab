from orchestrator.code_driven import CodeDrivenOrchestrator
from orchestrator.llm_driven  import LLMDrivenOrchestrator


def print_result(result: dict):
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    pipeline = result.get("pipeline", "unknown")
    print(f"Pipeline: {pipeline}")
    if result.get("session_id"):
        print(f"Session:  {result['session_id']}")
        print(f"Run:      {result['run_id']}")
    print()

    if pipeline == "code-driven":
        draft = result.get("draft", {})
        review = result.get("review", {})
        print(f"Title:    {draft.get('title', '')}")
        print(f"Content:\n{draft.get('content', '')}")
        print(f"\nReview verdict: {review.get('verdict', '')}")
        print(f"Strengths: {review.get('strengths', [])}")
        print(f"Improvements: {review.get('improvements', [])}")
    else:
        print(f"Summary:\n{result.get('summary', '')}")
        print(f"\nFull Draft:\n{result.get('draft', '')}")


def main():
    print("Stage 5 — Evals & Observability Demo")
    print("="*60)
    print("1. Code-Driven Orchestrator (deterministic pipeline)")
    print("2. LLM-Driven Orchestrator (agents-as-tools)")
    print("3. Both (compare outputs)\n")

    choice  = input("Choose (1/2/3): ").strip()
    topic   = input("Enter topic (e.g. 'AI agents'): ").strip()
    if not topic:
        topic = "AI agents"
    user_id = input("Enter user id (optional, press Enter to skip): ").strip() or None

    if choice in ("1", "3"):
        orchestrator = CodeDrivenOrchestrator()
        result = orchestrator.run(topic, user_id=user_id)
        print_result(result)

    if choice in ("2", "3"):
        orchestrator = LLMDrivenOrchestrator()
        result = orchestrator.run(topic, user_id=user_id)
        print_result(result)


if __name__ == "__main__":
    main()
