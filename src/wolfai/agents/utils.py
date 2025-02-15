import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@retry(
    retry=retry_if_exception_type(openai.RateLimitError),
    wait=wait_exponential(multiplier=2, min=1, max=10),  # Waits 2s, 4s, 8s, up to 10s
    stop=stop_after_attempt(5),  # Stop after 5 attempts
)
async def invoke_agent_with_retry(agent_executor, query):
    """Invoke the LangChain agent with retry logic for rate limits."""
    return await agent_executor.ainvoke(query)
