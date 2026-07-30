from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "景点AI问答机器人"

    # 数据库：开发默认 SQLite，生产改为 PostgreSQL+pgvector
    DATABASE_URL: str = "sqlite:///./app.db"

    # JWT
    JWT_SECRET: str = "summer-project-dev-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS（开发期放开，生产再收紧）
    CORS_ORIGINS: str = "*"

    # LLM（OpenAI 兼容）—— 通义千问 Qwen（可换 DeepSeek / 智谱 GLM / Kimi 等）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"
    LLM_MAX_TOKENS: int = 768

    # 预置管理员
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "123456"

    # ===== RAG / 知识库（M2）=====
    # 向量库持久化目录
    CHROMA_PERSIST_DIR: str = "data/chroma"
    # 嵌入模型（中文，本地 sentence-transformers）
    EMBEDDING_MODEL: str = "BAAI/bge-base-zh-v1.5"
    # 重排序模型（提升引用准确率）
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    # 中文分块参数（按字符数）
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    # 检索：向量召回数量 / 重排后保留数量
    RETRIEVE_TOP_K: int = 8
    RERANK_TOP_K: int = 4


settings = Settings()
