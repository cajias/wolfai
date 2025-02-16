"""Integration tests for Prolog chains using mock session."""

import pytest


@pytest.mark.asyncio
class TestPrologChainIntegration:
    """Integration tests for the Prolog reasoning chain."""

    async def test_socrates_example(self, mock_session):
        """Test the classic Socrates mortality example."""
        question = "If all humans are mortal and Socrates is human, is Socrates mortal?"
        
        # Execute the full chain
        result = await mock_session.get_prompt(
            "prolog-reasoning",
            {"question": question}
        )
        
        # Verify the message sequence
        messages = result.messages
        assert len(messages) >= 4  # Expect at least question, conversion, execution, interpretation
        
        # Check question
        assert messages[0].role == "user"
        assert messages[0].content.text == question
        
        # Check Prolog conversion
        assert messages[1].role == "assistant"
        prolog_code = messages[1].content.text
        assert "human(socrates)" in prolog_code
        assert "mortal(X) :- human(X)" in prolog_code
        
        # Check execution result
        assert messages[2].role == "assistant"
        assert "success" in messages[2].content.text.lower()
        
        # Check interpretation
        assert messages[-1].role == "assistant"
        assert "yes" in messages[-1].content.text.lower()

    async def test_grandparent_example(self, mock_session):
        """Test reasoning about family relationships."""
        question = "If John is a parent of Mary, and Mary is a parent of Bob, is John a grandparent of Bob?"
        
        result = await mock_session.get_prompt(
            "prolog-reasoning",
            {"question": question}
        )
        
        messages = result.messages
        
        # Verify Prolog code contains necessary predicates
        prolog_text = messages[1].content.text
        assert "parent(john, mary)" in prolog_text
        assert "parent(mary, bob)" in prolog_text
        assert "grandparent" in prolog_text
        
        # Verify execution and result
        assert any(
            msg.role == "assistant" and "success" in msg.content.text.lower()
            for msg in messages
        )
        assert messages[-1].role == "assistant"
        assert "yes" in messages[-1].content.text.lower()

    async def test_independent_tools(self, mock_session):
        """Test using the tools independently."""
        # First convert to Prolog
        conversion = await mock_session.get_prompt(
            "convert-to-prolog",
            {"question": "If all birds can fly, and tweety is a bird, can tweety fly?"}
        )
        
        assert len(conversion.messages) == 1
        prolog_code = conversion.messages[0].content.text
        assert "bird(tweety)" in prolog_code
        assert "fly(X) :- bird(X)" in prolog_code
        
        # Then execute the Prolog code
        execution = await mock_session.call_tool(
            "consult",
            {"code": prolog_code}
        )
        
        assert execution["success"]
        assert len(execution["solutions"]) > 0

    async def test_error_handling(self, mock_session):
        """Test handling of various error conditions."""
        # Test with unknown question pattern
        result = await mock_session.get_prompt(
            "prolog-reasoning",
            {"question": "This is not a valid logical question"}
        )
        
        # Should still get a valid response structure
        assert len(result.messages) >= 2
        
        # Test with invalid Prolog code
        execution = await mock_session.call_tool(
            "consult",
            {"code": "this is not valid Prolog code"}
        )
        
        assert not execution["success"]
        assert execution["error"] is not None

    async def test_prompt_chaining(self, mock_session):
        """Test chaining multiple prompts together manually."""
        question = "If all humans are mortal and Socrates is human, is Socrates mortal?"
        
        # Step 1: Convert to Prolog
        conversion = await mock_session.get_prompt(
            "convert-to-prolog",
            {"question": question}
        )
        prolog_code = conversion.messages[0].content.text
        
        # Step 2: Execute the code
        execution = await mock_session.call_tool(
            "consult",
            {"code": prolog_code}
        )
        
        # Step 3: Interpret results
        interpretation = await mock_session.get_prompt(
            "interpret-results",
            {
                "question": question,
                "prolog_code": prolog_code,
                "results": str(execution)
            }
        )
        
        # Verify the complete chain
        assert prolog_code and "mortal" in prolog_code
        assert execution["success"]
        assert interpretation.messages[-1].content.text