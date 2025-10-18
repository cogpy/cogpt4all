#!/usr/bin/env python3
"""
OpenCog Autonomous Agent Orchestrator Demo

This script demonstrates how to use the OpenCog-inspired agent orchestrator
with GPT4All models for autonomous agent behavior.
"""

import time
import sys
import os

# Add the parent directory to the path so we can import gpt4all
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gpt4all import (
    AgentOrchestrator, 
    ChatAgent, 
    TaskAgent, 
    AtomSpace, 
    AtomType, 
    Atom,
    create_example_orchestrator
)


def demo_basic_atomspace():
    """Demonstrate basic AtomSpace functionality."""
    print("=== AtomSpace Demo ===")
    
    atomspace = AtomSpace()
    
    # Create some basic atoms
    concept_atom = Atom(
        atom_type=AtomType.CONCEPT,
        name="AI_System",
        value="Advanced AI System",
        confidence=0.9
    )
    
    agent_atom = Atom(
        atom_type=AtomType.AGENT,
        name="ChatAgent_1",
        value="conversational_agent",
        metadata={"capabilities": ["chat", "reasoning"]}
    )
    
    goal_atom = Atom(
        atom_type=AtomType.GOAL,
        name="HelpUser",
        value="Assist user with their questions and tasks",
        confidence=0.95
    )
    
    # Add atoms to atomspace
    atomspace.add_atom(concept_atom)
    atomspace.add_atom(agent_atom)
    atomspace.add_atom(goal_atom)
    
    # Create relationships
    atomspace.create_link(agent_atom.atom_id, goal_atom.atom_id, "has_goal")
    
    # Query atoms
    agents = atomspace.find_atoms_by_type(AtomType.AGENT)
    print(f"Found {len(agents)} agent atoms")
    
    goals = atomspace.find_atoms_by_type(AtomType.GOAL)
    print(f"Found {len(goals)} goal atoms")
    
    # Find by name
    ai_concepts = atomspace.find_atoms_by_name("AI_System")
    print(f"Found AI concepts: {[a.name for a in ai_concepts]}")
    
    print()


def demo_agent_orchestrator():
    """Demonstrate agent orchestrator functionality."""
    print("=== Agent Orchestrator Demo ===")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(max_agents=3)
    
    # Create agents without GPT4All (for demo purposes)
    chat_agent_id = orchestrator.create_agent(ChatAgent, "DemoChat", None)
    task_agent_id = orchestrator.create_agent(TaskAgent, "DemoTask", None)
    
    # Get agents and add goals
    chat_agent = orchestrator.get_agent(chat_agent_id)
    chat_agent.add_goal("Greet users warmly")
    chat_agent.add_goal("Answer questions helpfully")
    
    task_agent = orchestrator.get_agent(task_agent_id)
    task_agent.add_goal("Organize daily tasks")
    task_agent.add_goal("Provide productivity tips")
    
    # Show initial status
    print("Initial agent status:")
    status = orchestrator.get_agent_status()
    for agent_id, info in status.items():
        print(f"  {info['name']}: {info['goals']} goals, state={info['state']}")
    
    print("\nAtomSpace statistics:")
    stats = orchestrator.get_atomspace_stats()
    print(f"  Total atoms: {stats['total_atoms']}")
    print(f"  Type distribution: {stats['type_distribution']}")
    
    # Run a few steps
    print("\nRunning agent steps...")
    for i in range(3):
        print(f"\n--- Step {i+1} ---")
        results = orchestrator.step_all_agents()
        for agent_id, result in results.items():
            agent_name = orchestrator.get_agent(agent_id).name
            print(f"  {agent_name}: {result}")
    
    print()


def demo_interactive_chat():
    """Demonstrate interactive chat with agents (without GPT4All)."""
    print("=== Interactive Agent Demo ===")
    print("This demo shows agent interaction without GPT4All models")
    print("(For full functionality, configure GPT4All models)")
    
    orchestrator = AgentOrchestrator(max_agents=2)
    
    # Create a chat agent
    chat_agent_id = orchestrator.create_agent(ChatAgent, "Assistant", None)
    chat_agent = orchestrator.get_agent(chat_agent_id)
    chat_agent.add_goal("Be helpful and friendly")
    
    print(f"\nChat agent '{chat_agent.name}' is ready!")
    print("The agent will simulate responses since no GPT4All model is loaded.")
    
    # Simulate some interactions
    messages = [
        "Hello, how are you?",
        "What can you help me with?",
        "Tell me about artificial intelligence."
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        
        # This will use the mock response since no GPT4All model is available
        response = chat_agent.respond_to_message(message, "user")
        print(f"Assistant: {response}")
        
        # Show agent's memory
        if chat_agent.memory:
            print(f"  (Agent remembered: {chat_agent.memory[-1]})")
    
    print(f"\nConversation history length: {len(chat_agent.conversation_history)}")
    print()


def demo_with_gpt4all():
    """Demonstrate with actual GPT4All model if available."""
    print("=== GPT4All Integration Demo ===")
    
    try:
        # Try to create the example orchestrator with GPT4All
        orchestrator = create_example_orchestrator()
        print("Successfully created orchestrator with GPT4All integration!")
        
        # Get the chat agent
        agents = list(orchestrator.agents.values())
        chat_agents = [a for a in agents if isinstance(a, ChatAgent)]
        
        if chat_agents and chat_agents[0].gpt4all:
            chat_agent = chat_agents[0]
            print(f"\nTesting GPT4All integration with agent '{chat_agent.name}'...")
            
            # Test a simple interaction
            test_message = "Hello! Can you tell me about yourself?"
            print(f"\nUser: {test_message}")
            
            response = chat_agent.respond_to_message(test_message)
            print(f"{chat_agent.name}: {response}")
            
            # Show agent stats
            print(f"\nAgent Statistics:")
            print(f"  Goals: {len(chat_agent.goals)}")
            print(f"  Memories: {len(chat_agent.memory)}")
            print(f"  Conversation history: {len(chat_agent.conversation_history)}")
            
        else:
            print("GPT4All model not available for agents.")
        
    except Exception as e:
        print(f"Could not create GPT4All orchestrator: {e}")
        print("This is expected if no GPT4All models are downloaded locally.")
    
    print()


def main():
    """Run all demos."""
    print("OpenCog Autonomous Agent Orchestrator Demo")
    print("=" * 50)
    print()
    
    # Run demos
    demo_basic_atomspace()
    demo_agent_orchestrator()
    demo_interactive_chat()
    demo_with_gpt4all()
    
    print("Demo completed!")
    print("\nTo use with actual GPT4All models:")
    print("1. Ensure you have GPT4All models downloaded")
    print("2. Install gpt4all package: pip install gpt4all")
    print("3. Run with proper model names")


if __name__ == "__main__":
    main()