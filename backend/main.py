from backend.core.chat_service import ChatService



chat_service = ChatService()
while True:
    user_input = input("用户：")
    if user_input.strip().lower()in["exit", "quit","退出","结束"]:
        print("对话结束")
        break

    answer = chat_service.chat(user_input)
    print("AI: ",answer)
    print("="*80)
