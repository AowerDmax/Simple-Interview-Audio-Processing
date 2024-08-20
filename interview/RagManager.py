import asyncio
from meilisearch import Client
from DialogManager import DialogManager
from Config import Config
import json
class RagManager:
    def __init__(self):
        self.dialog = DialogManager()
        self.config = Config()
        self.meilisearch_client = Client(f"http://{self.config.MEILISEARCH_HOST}:{self.config.MEILISEARCH_PORT}")

    async def query_meilisearch(self):
        query_object = self.dialog.get_last_interviewer()
        query_text = query_object['text']
        print(f"query_text: {query_text}")
        index = self.meilisearch_client.index('qa_pairs')
        
        results = index.search(query_text, {
            'limit': self.config.MEILISEARCH_DEEP
        })
        answers = [hit['a'] for hit in results['hits'] if 'a' in hit]
        return answers

async def main():
    rag = RagManager()
    answers = await rag.query_meilisearch()
    for ans in answers:
        print(ans)

if __name__ == '__main__':
    asyncio.run(main())