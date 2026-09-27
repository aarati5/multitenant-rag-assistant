from src.documents import DOCUMENTS
from src.vector_store import build_store, search
from src.audit import log_access, view_log
from src.qa_agent import generate_answer

VALID_ROLES = ["hr", "engineering", "finance"]

def run():
    print("=" * 60)
    print("MULTI-TENANT RAG ASSISTANT (Permission-Aware)")
    print("=" * 60)

    print("\nIndexing company documents...")
    build_store(DOCUMENTS)

    user_name = input("\nEnter your name: ").strip()
    user_role = input(f"Enter your role ({'/'.join(VALID_ROLES)}): ").strip().lower()

    if user_role not in VALID_ROLES:
        print("Invalid role. Defaulting to no access.")
        user_role = "none"

    print(f"\nLogged in as {user_name} ({user_role})")

    while True:
        print("\n" + "-" * 60)
        print("1. Ask a question")
        print("2. View audit log")
        print("3. Exit")
        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            query = input("\nYour question: ").strip()
            results = search(query, user_role, top_k=2)

            retrieved_ids = [d["id"] for d in results]
            log_access(user_name, user_role, query, retrieved_ids)

            print(f"\n[Accessible documents retrieved: {retrieved_ids}]")
            answer = generate_answer(query, results)
            print("\nAnswer:")
            print(answer)

        elif choice == "2":
            print("\n" + view_log())

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    run()