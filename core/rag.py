"""
RAG (Retrieval Augmented Generation) система для ассистента.

Использует ChromaDB для векторной БД и sentence-transformers для embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    chromadb = None
    SentenceTransformer = None


class RAGSystem:
    """
    Система Retrieval Augmented Generation.

    Использует локальную векторную БД для поиска релевантных документов.
    """

    def __init__(
        self,
        db_path: str = "rag_db",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        top_k: int = 5,
    ):
        """
        Инициализация RAG системы.

        Args:
            db_path: Путь к БД ChromaDB
            model_name: Имя модели для embeddings
            top_k: Количество результатов для поиска
        """
        self.db_path = db_path
        self.top_k = top_k
        self.is_available = False

        logger.info("🧠 Инициализация RAG системы")

        if chromadb is None or SentenceTransformer is None:
            logger.warning("⚠️ ChromaDB или sentence-transformers не установлены")
            return

        try:
            # Инициализируем ChromaDB
            logger.info(f"📥 Загрузка модели embeddings ({model_name})...")
            self.embedding_model = SentenceTransformer(model_name)

            # Создаем клиент ChromaDB
            settings = Settings(
                chroma_db_impl="duckdb",
                persist_directory=db_path,
                anonymized_telemetry=False,
            )
            self.client = chromadb.Client(settings)

            # Создаем коллекции
            self.documents_collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"},
            )

            self.memory_collection = self.client.get_or_create_collection(
                name="memory",
                metadata={"hnsw:space": "cosine"},
            )

            self.is_available = True
            logger.info("✅ RAG система инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAG: {e}")
            self.is_available = False

    def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Добавить документ в RAG.

        Args:
            content: Содержимое документа
            metadata: Метаданные документа
            doc_id: ID документа (генерируется если не указано)

        Returns:
            ID документа
        """
        if not self.is_available:
            logger.warning("⚠️ RAG система недоступна")
            return ""

        try:
            # Генерируем ID если не указано
            if not doc_id:
                import uuid
                doc_id = str(uuid.uuid4())

            # Создаем embedding
            embedding = self.embedding_model.encode(content).tolist()

            # Подготавливаем метаданные
            if metadata is None:
                metadata = {}

            metadata["added_at"] = datetime.now().isoformat()
            metadata["content_length"] = len(content)

            # Добавляем в коллекцию
            self.documents_collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[content[:500]],  # Сохраняем первые 500 символов
            )

            logger.info(f"✅ Документ добавлен: {doc_id} ({len(content)} символов)")
            return doc_id

        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа: {e}")
            return ""

    def search_documents(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Поиск документов в RAG.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            filters: Фильтры по метаданным

        Returns:
            Список найденных документов
        """
        if not self.is_available:
            logger.warning("⚠️ RAG система недоступна")
            return []

        try:
            if top_k is None:
                top_k = self.top_k

            # Создаем embedding для запроса
            query_embedding = self.embedding_model.encode(query).tolist()

            # Ищем в коллекции
            results = self.documents_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
            )

            # Форматируем результаты
            documents = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    documents.append(
                        {
                            "id": doc_id,
                            "content": results["documents"][0][i] if results["documents"] else "",
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 1.0,
                        }
                    )

            logger.debug(f"🔍 Найдено {len(documents)} документов по запросу")
            return documents

        except Exception as e:
            logger.error(f"❌ Ошибка поиска документов: {e}")
            return []

    def add_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
    ) -> str:
        """
        Добавить воспоминание в RAG.

        Args:
            content: Содержимое воспоминания
            memory_type: Тип памяти (episodic, semantic, procedural)
            importance: Важность (0-1)

        Returns:
            ID воспоминания
        """
        if not self.is_available:
            return ""

        try:
            import uuid

            memory_id = str(uuid.uuid4())
            embedding = self.embedding_model.encode(content).tolist()

            self.memory_collection.upsert(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[{
                    "type": memory_type,
                    "importance": importance,
                    "timestamp": datetime.now().isoformat(),
                }],
                documents=[content[:500]],
            )

            logger.info(f"💾 Воспоминание добавлено: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"❌ Ошибка добавления воспоминания: {e}")
            return ""

    def search_memory(
        self,
        query: str,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Поиск воспоминаний.

        Args:
            query: Поисковый запрос
            memory_type: Фильтр по типу памяти
            min_importance: Минимальная важность

        Returns:
            Список найденных воспоминаний
        """
        if not self.is_available:
            return []

        try:
            filters = {}
            if memory_type:
                filters["type"] = memory_type

            # Ищем с фильтром важности в post-processing
            results = self.search_documents(query, top_k=self.top_k * 2)

            # Фильтруем по важности
            filtered = []
            for doc in results:
                importance = doc["metadata"].get("importance", 0.0)
                if importance >= min_importance:
                    filtered.append(doc)

            return filtered[:self.top_k]

        except Exception as e:
            logger.error(f"❌ Ошибка поиска воспоминаний: {e}")
            return []

    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Получить контекст для запроса.

        Args:
            query: Поисковый запрос
            max_tokens: Максимум токенов для контекста

        Returns:
            Отформатированный контекст
        """
        try:
            # Ищем документы
            documents = self.search_documents(query)
            memories = self.search_memory(query)

            context = "📚 Контекст из памяти ассистента:\n\n"

            token_count = 0

            # Добавляем документы
            if documents:
                context += "📄 Релевантные документы:\n"
                for doc in documents:
                    doc_text = f"- {doc['content']}\n"
                    if token_count + len(doc_text.split()) < max_tokens:
                        context += doc_text
                        token_count += len(doc_text.split())
                context += "\n"

            # Добавляем воспоминания
            if memories:
                context += "💭 Релевантные воспоминания:\n"
                for mem in memories:
                    mem_text = f"- {mem['content']}\n"
                    if token_count + len(mem_text.split()) < max_tokens:
                        context += mem_text
                        token_count += len(mem_text.split())

            return context

        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return ""

    def import_documents(self, directory: str) -> int:
        """
        Импортировать документы из директории.

        Args:
            directory: Путь к директории

        Returns:
            Количество импортированных документов
        """
        if not self.is_available:
            return 0

        try:
            count = 0
            doc_path = Path(directory)

            # Поддерживаемые форматы
            supported_formats = {
                ".txt": self._read_txt,
                ".pdf": self._read_pdf,
                ".docx": self._read_docx,
                ".md": self._read_txt,
            }

            for file_path in doc_path.rglob("*"):
                if file_path.suffix in supported_formats:
                    try:
                        content = supported_formats[file_path.suffix](file_path)
                        self.add_document(
                            content,
                            metadata={"source": str(file_path)},
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка импорта {file_path}: {e}")

            logger.info(f"✅ Импортировано {count} документов")
            return count

        except Exception as e:
            logger.error(f"❌ Ошибка импорта документов: {e}")
            return 0

    @staticmethod
    def _read_txt(file_path: Path) -> str:
        """Прочитать TXT файл."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _read_pdf(file_path: Path) -> str:
        """Прочитать PDF файл."""
        try:
            from PyPDF2 import PdfReader

            text = ""
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            logger.warning(f"⚠️ Ошибка чтения PDF: {e}")
            return ""

    @staticmethod
    def _read_docx(file_path: Path) -> str:
        """Прочитать DOCX файл."""
        try:
            from docx import Document

            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text
        except Exception as e:
            logger.warning(f"⚠️ Ошибка чтения DOCX: {e}")
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику RAG."""
        try:
            if not self.is_available:
                return {"available": False}

            return {
                "available": True,
                "documents_count": self.documents_collection.count() if hasattr(
                    self.documents_collection, "count"
                ) else 0,
                "memory_count": self.memory_collection.count() if hasattr(
                    self.memory_collection, "count"
                ) else 0,
                "model": "all-MiniLM-L6-v2",
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения статистики: {e}")
            return {}

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"RAGSystem(available={self.is_available})"