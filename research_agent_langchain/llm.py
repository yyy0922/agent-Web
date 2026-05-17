from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel


def create_llm(model: str = "gpt-4o-mini", api_key: str = None, base_url: str = None, temperature: float = 0.3) -> BaseChatModel:
    kwargs = {"model": model, "temperature": temperature}
    if api_key:
        kwargs["openai_api_key"] = api_key
    if base_url:
        kwargs["openai_api_base"] = base_url
    return ChatOpenAI(**kwargs)
