from typing import Dict, Any

import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@retry(
    retry=retry_if_exception_type(openai.RateLimitError),
    wait=wait_exponential(multiplier=2, min=1, max=10),  # Waits 2s, 4s, 8s, up to 10s
    stop=stop_after_attempt(5),  # Stop after 5 attempts
)

async def invoke_agent_with_retry(agent_executor, query)->Dict[str, Any]:
    """Invoke the LangChain agent with retry logic for rate limits."""
    # The new create_agent API expects messages in a specific format
    if isinstance(query, str):
        result = await agent_executor.ainvoke({"messages": [("user", query)]})
        # Extract the response from the result
        if "messages" in result:
            # Get the last message which should be the assistant's response
            last_message = result["messages"][-1]
            return {"output": last_message.content if hasattr(last_message, 'content') else str(last_message)}
        return {"output": str(result)}
    return await agent_executor.ainvoke(query)
