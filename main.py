import sys
from src.ingest import run_ingestion
from src.rag_pipeline import GraphRAG

def main():
    # Kiểm tra tham số dòng lệnh
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        print("🔄 Chế độ: Nạp dữ liệu (Ingestion)...")
        run_ingestion()
        return

    # Chế độ mặc định: Chat
    rag = GraphRAG()
    print("\n" + "="*50)
    print("MOVIE RECOMMENDER SYSTEM (GraphRAG + Gemini)")
    print("Using: Neo4j (Graph) + Qdrant (Vector)")
    print("="*50)
    print("Gõ 'exit', 'quit' hoặc 'bye' để thoát.\n")
    
    try:
        while True:
            user_input = input("Bạn (Hỏi về phim): ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Tạm biệt!")
                break
            
            if not user_input.strip():
                continue
                
            response = rag.query(user_input)
            print(f"\n🤖 Gemini: {response}\n" + "-"*50)
            
    except KeyboardInterrupt:
        print("\n👋 Đã dừng chương trình.")
    finally:
        rag.close()

if __name__ == "__main__":
    main()