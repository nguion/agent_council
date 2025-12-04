
import asyncio
from agent_council.core.council_runner import CouncilRunner

async def verify_persona():
    print("Starting Persona Verification...")
    
    # Simulate an agent config from the Council Builder
    agent_config = {
        "name": "Captain Ahab",
        "persona": "You are Captain Ahab, obsessed with the white whale. You speak in 19th-century nautical terms.",
        "reasoning_effort": "medium",
        "enable_web_search": False
    }
    
    # The prompt we normally send
    prompt = "Who are you and what is your goal?"
    
    print(f"1. Configured Persona: {agent_config['persona']}")
    print(f"2. Prompt: {prompt}")
    
    # Run using the CouncilRunner logic
    print("\n3. Executing Agent...")
    result = await CouncilRunner.run_single_agent(agent_config, prompt)
    
    print("\n4. Result:")
    print(f"   Agent Name: {result['agent_name']}")
    print(f"   Response:\n{result['response']}")
    
    # Verification
    response_lower = result['response'].lower()
    if "ahab" in response_lower or "whale" in response_lower:
        print("\n✅ SUCCESS: Agent adopted the persona.")
    else:
        print("\n❌ FAILURE: Agent did not adopt the persona.")

if __name__ == "__main__":
    asyncio.run(verify_persona())
