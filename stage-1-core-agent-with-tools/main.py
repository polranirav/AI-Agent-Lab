from agent.loop import run_agent

def main():
    print("=== Stage 1 Agent — Single Agent + Tool Use ===")
    print("Type 'exit' to quit. \n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("goodbye")
            break


        answer = run_agent(user_input)
        print("\nAgent: ", answer)
        print("\n" + "=" * 50)


if __name__ == "__main__":
    main()

        