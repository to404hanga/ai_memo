from datetime import UTC
import hashlib

from langchain.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model.memo_store import Memo


class Ingester:
    embeddings: Embeddings
    vectorstore: VectorStore

    def __init__(self, embeddings: Embeddings, vectorstore: VectorStore):
        self.embeddings = embeddings
        self.vectorstore = vectorstore

    def __process(self, memo: Memo) -> tuple[list[Document], list[str]]:
        doc = Document(
            page_content=memo.content,
            metadata={
                "id": memo.id,
                "deadline": memo.deadline.astimezone(UTC),
                "done": memo.done,
                "title": memo.title,
                "is_urgent": memo.is_urgent,
            },
        )
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=100,
            is_separator_regex=True,
            separators=["\n\n", "\n", r"(?<=[。！？])", " ", ""],
        )
        docs = text_splitter.split_documents([doc])
        ids = [hashlib.md5(doc.page_content.encode()).hexdigest() for doc in docs]
        return docs, ids

    async def create(self, memo: Memo):
        await self.vectorstore.adelete(filter={"id": memo.id})
        docs, ids = self.__process(memo)
        await self.vectorstore.aadd_documents(documents=docs, ids=ids)

    async def delete(
        self, document_ids: list[str] | None = None, filter: dict | None = None
    ):
        await self.vectorstore.adelete(ids=document_ids, filter=filter)
