"""Main entry point to run the Layer 1 Personal Assistant."""

import asyncio
import os
import sys
from assistant.agent import create_personal_assistant
from assistant.tools.briefing_tool import generate_morning_briefing
from gateway.router import gateway
from evolver.engine import self_evolver
from rag import list_indexed_documents
from mcp_hub import list_mcp_tools

from gateway.config import load_env

load_env()

async def run_interactive_assistant():
    print("=" * 60)
    print("[+] Hermit Agent - Autonomous Multi-Layer System")
    print("    Layer 1: Personal Assistant (Memory, Calendar, Tasks)")
    print("    Layer 2: Self-Evolver & Universal API Gateway")
    print("    Layer 3: Model Context Protocol (MCP) Hub & RAG Engine")
    print("    Layer 4: Autonomous Multi-Agent Swarm (Research, Coder, Reviewer)")
    print("    Layer 5: Web Scraping, Browser Search & Multi-Model Coding")
    print("=" * 60)
    
    # Show Gateway, Evolver, RAG and MCP status
    active_providers = gateway.get_active_providers()
    print(f"[*] Gateway Providers Active: {', '.join(active_providers) if active_providers else 'None configured'}")
    print(f"[*] {self_evolver.get_evolution_summary()}")
    print(f"[*] RAG: {list_indexed_documents().replace(chr(10), ' | ')}")
    print(f"[*] MCP Hub: filesystem, system_info connected")
    print(f"[*] Swarm: Research, Engineering, QA Reviewer ready")
    
    # Show initial daily briefing
    print("\n" + generate_morning_briefing() + "\n")
    print("Type your message (or 'exit' to quit):\n")
    
    assistant = create_personal_assistant()
    
    async with assistant as ag:
        while True:
            try:
                # Use asyncio.to_thread so blocking input() doesn't freeze the event loop
                user_input = await asyncio.to_thread(input, "You > ")
                user_input = user_input.strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Goodbye! Have a productive day.")
                    break
                    
                print("\nAssistant is thinking...")
                response = await ag.chat(user_input)
                
                # Extract response text asynchronously
                if hasattr(response, "text"):
                    if callable(response.text):
                        import inspect
                        if inspect.iscoroutinefunction(response.text) or asyncio.iscoroutine(response.text()):
                            reply_text = await response.text()
                        else:
                            reply_text = response.text()
                    else:
                        reply_text = response.text
                else:
                    reply_text = str(response)
                    
                print(f"\nAssistant:\n{reply_text}\n")
                
                # Autonomous Layer 2 Evolution Check (Observer)
                evolution_result = await self_evolver.evolve(
                    current_instructions="",
                    user_input=user_input,
                    agent_output=reply_text
                )
                if evolution_result.get("evolved"):
                    print(f"[*] [SELF-EVOLVED] Version updated to v{evolution_result['version']} (Strategy: {evolution_result['strategy']})\n")
                    
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended.")
                break
            except Exception as e:
                print(f"\n⚠️ Error: {e}\n")

if __name__ == "__main__":
    # Check for GEMINI_API_KEY
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ Warning: GEMINI_API_KEY is not set in environment variables.")
        print("Set it using: $env:GEMINI_API_KEY = 'your_key' (PowerShell) or via .env")
    
    asyncio.run(run_interactive_assistant())
