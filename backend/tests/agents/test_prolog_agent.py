import asyncio
import logging
import os
import sys
import subprocess
import threading
import queue
import traceback
import pytest
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from mcp import StdioServerParameters

from wolfai.agents import PrologAgent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def capture_process_output(process, output_queue):
    """Capture and log process output in real-time."""
    try:
        for line in iter(process.stdout.readline, ""):
            if isinstance(line, bytes):  # Ensure decoding if necessary
                line = line.decode("utf-8")
            line = line.strip()
            output_queue.put(line)
            logger.debug(f"PROCESS OUTPUT: {line}")
    except Exception as e:
        logger.error(f"Process output capture error: {e}")
        logger.error(traceback.format_exc())
    finally:
        process.stdout.close()

@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv("OPENAI_API_KEY") is None, reason="OPENAI_API_KEY not set")
async def test_prolog_agent_initialization(tmp_path):
    """Detailed integration test for Prolog MCP server initialization."""
    load_dotenv()  # Load environment variables

    # Create output queue for process logging
    output_queue = queue.Queue()

    # Prepare a unique log file for process logging
    log_file = tmp_path / "server_debug.log"

    # Start the Prolog MCP server as a subprocess with detailed logging
    server_command = [
        sys.executable,
        "-m", "wolfai.tools.pl.prolog_mcp_server"
    ]

    server_process = subprocess.Popen(
        server_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True  # Ensures output is read as text
    )

    # Thread to capture process output
    output_thread = threading.Thread(
        target=capture_process_output,
        args=(server_process, output_queue)
    )
    output_thread.start()

    # Server initialization parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "wolfai.tools.pl.prolog_mcp_server"],
        env=dict(os.environ)
    )

    try:
        # Extensive timeout for comprehensive debugging
        agent = PrologAgent(
                ChatOpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    model="gpt-3.5-turbo",
                    timeout=30.0,
                    max_retries=1
                ),
                server_params
            )
        await asyncio.wait_for(agent.initialize(),timeout=2000.0)

        # Verify agent initialization
        assert agent is not None, "Agent should be successfully created"
        assert agent.agent_executor is not None, "Executor should be successfully created"

        logger.info("Prolog agent initialization successful")

    except asyncio.TimeoutError:
        # Capture and log all process output on timeout
        logger.error("Agent initialization timed out")
        logger.error("Process Output Log:")
        while not output_queue.empty():
            log_line = output_queue.get()
            logger.error(log_line)

        # Write process output to debug log file
        with open(log_file, 'w') as f:
            while not output_queue.empty():
                f.write(output_queue.get() + "\n")

        pytest.fail(f"Agent initialization timed out. See debug log: {log_file}")

    except Exception as e:
        logger.error(f"Unexpected error during agent initialization: {e}")
        logger.error(traceback.format_exc())

        logger.error("Process Output Log:")
        while not output_queue.empty():
            log_line = output_queue.get()
            logger.error(log_line)

        # Write process output to debug log file
        with open(log_file, 'w') as f:
            while not output_queue.empty():
                f.write(output_queue.get() + "\n")

        pytest.fail(f"Prolog agent initialization failed: {str(e)}. See debug log: {log_file}")

    finally:
        # Ensure process is terminated
        server_process.terminate()
        server_process.wait(timeout=5)  # Ensure graceful shutdown
        output_thread.join()
