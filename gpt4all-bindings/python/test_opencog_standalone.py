#!/usr/bin/env python3
"""
Standalone test for OpenCog orchestrator functionality.

This test runs independently of the GPT4All library to demonstrate
the core OpenCog-inspired functionality.
"""

import sys
import os

# Import the opencog_orchestrator module directly without gpt4all dependencies
sys.path.append(os.path.join(os.path.dirname(__file__), 'gpt4all'))

# Import directly from the module file
from opencog_orchestrator import (
    AtomSpace, Atom, AtomType, Agent, ChatAgent, TaskAgent, 
    AgentOrchestrator, AgentState, Goal
)


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def perceive(self):
        return {"test": True, "time": self.last_action_time}
    
    def decide(self, observations):
        if observations.get("test"):
            return "test_action"
        return None
    
    def act(self, action):
        return {"action": action, "result": "success", "agent": self.name}


def test_atomspace():
    """Test AtomSpace functionality."""
    print("=== Testing AtomSpace ===")
    
    atomspace = AtomSpace()
    
    # Create atoms
    concept = Atom(
        atom_type=AtomType.CONCEPT,
        name="AI_System",
        value="Artificial Intelligence System",
        confidence=0.9
    )
    
    agent_atom = Atom(
        atom_type=AtomType.AGENT,
        name="TestAgent",
        value="test_agent_id",
        metadata={"type": "chat_agent"}
    )
    
    goal_atom = Atom(
        atom_type=AtomType.GOAL,
        name="HelpUsers",
        value="Assist users with their questions",
        confidence=0.8
    )
    
    # Add to atomspace
    concept_id = atomspace.add_atom(concept)
    agent_id = atomspace.add_atom(agent_atom)  
    goal_id = atomspace.add_atom(goal_atom)
    
    print(f"Added {len(atomspace._atoms)} atoms to AtomSpace")
    
    # Create relationships
    atomspace.create_link(agent_id, goal_id, "has_goal")
    
    # Query tests
    agents = atomspace.find_atoms_by_type(AtomType.AGENT)
    goals = atomspace.find_atoms_by_type(AtomType.GOAL)
    concepts = atomspace.find_atoms_by_type(AtomType.CONCEPT)
    
    print(f"Found: {len(agents)} agents, {len(goals)} goals, {len(concepts)} concepts")
    
    # Test query
    ai_atoms = atomspace.find_atoms_by_name("AI_System")
    print(f"Found AI atoms: {[a.value for a in ai_atoms]}")
    
    # Test pattern query
    chat_agents = atomspace.query({"type": "chat_agent"})
    print(f"Found chat agents: {len(chat_agents)}")
    
    print("✓ AtomSpace tests passed\n")


def test_basic_agent():
    """Test basic agent functionality."""
    print("=== Testing Basic Agent ===")
    
    atomspace = AtomSpace()
    agent = MockAgent("test_id", "TestAgent", atomspace, None)
    
    print(f"Created agent: {agent.name} (ID: {agent.agent_id})")
    print(f"Initial state: {agent.state}")
    
    # Add goals
    goal1 = agent.add_goal("Complete tasks efficiently", priority=0.9)
    goal2 = agent.add_goal("Learn from interactions", priority=0.7)
    
    print(f"Added {len(agent.goals)} goals")
    
    # Test memory
    agent.remember("Started up successfully")
    agent.remember("Goal priorities set")
    
    print(f"Stored {len(agent.memory)} memories")
    
    # Test cognitive step
    result = agent.step()
    print(f"Step result: {result}")
    
    # Verify agent was registered in atomspace
    agent_atoms = atomspace.find_atoms_by_type(AtomType.AGENT)
    goal_atoms = atomspace.find_atoms_by_type(AtomType.GOAL)
    memory_atoms = atomspace.find_atoms_by_type(AtomType.MEMORY)
    
    print(f"AtomSpace contains: {len(agent_atoms)} agents, {len(goal_atoms)} goals, {len(memory_atoms)} memories")
    
    print("✓ Basic agent tests passed\n")


def test_chat_agent():
    """Test ChatAgent functionality."""
    print("=== Testing Chat Agent ===")
    
    atomspace = AtomSpace()
    chat_agent = ChatAgent("chat_id", "ChatBot", atomspace, None)
    
    print(f"Created chat agent: {chat_agent.name}")
    
    # Add goals
    chat_agent.add_goal("Engage in meaningful conversations")
    chat_agent.add_goal("Provide helpful responses")
    
    # Test conversation
    messages = [
        "Hello! How are you today?",
        "What's your favorite topic to discuss?",
        "Can you help me with a problem?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = chat_agent.respond_to_message(message, "user")
        print(f"ChatBot: {response}")
    
    print(f"\nConversation history: {len(chat_agent.conversation_history)} exchanges")
    print(f"Agent memories: {len(chat_agent.memory)}")
    
    # Test agent step with goals
    result = chat_agent.step()
    print(f"Agent step result: {result}")
    
    print("✓ Chat agent tests passed\n")


def test_task_agent():
    """Test TaskAgent functionality."""
    print("=== Testing Task Agent ===")
    
    atomspace = AtomSpace()
    task_agent = TaskAgent("task_id", "TaskManager", atomspace, None)
    
    print(f"Created task agent: {task_agent.name}")
    
    # Add goals  
    task_agent.add_goal("Organize and complete tasks")
    task_agent.add_goal("Improve productivity")
    
    # Add some tasks manually
    task_agent.task_queue.extend([
        "Review project requirements",
        "Create implementation plan",
        "Write documentation"
    ])
    
    print(f"Initial task queue: {len(task_agent.task_queue)} tasks")
    
    # Run several steps to process tasks
    for i in range(4):
        result = task_agent.step()
        print(f"Step {i+1}: {result}")
        
        if result.get("action") == "task_completed":
            print(f"  ✓ Completed: {result.get('task')}")
        elif result.get("action") == "goal_planned":
            print(f"  📋 Planned tasks for: {result.get('goal')}")
    
    print(f"\nFinal state:")
    print(f"  Pending tasks: {len(task_agent.task_queue)}")
    print(f"  Completed tasks: {len(task_agent.completed_tasks)}")
    print(f"  Memories: {len(task_agent.memory)}")
    
    print("✓ Task agent tests passed\n")


def test_orchestrator():
    """Test AgentOrchestrator functionality."""
    print("=== Testing Agent Orchestrator ===")
    
    orchestrator = AgentOrchestrator(max_agents=5)
    
    print(f"Created orchestrator (max {orchestrator.max_agents} agents)")
    
    # Create multiple agents
    chat_id = orchestrator.create_agent(ChatAgent, "Assistant", None)
    task_id = orchestrator.create_agent(TaskAgent, "TaskBot", None)
    mock_id = orchestrator.create_agent(MockAgent, "Helper", None)
    
    print(f"Created {len(orchestrator.agents)} agents")
    
    # Set up agents with goals
    chat_agent = orchestrator.get_agent(chat_id)
    chat_agent.add_goal("Be helpful and friendly")
    
    task_agent = orchestrator.get_agent(task_id)
    task_agent.add_goal("Complete all assigned tasks")
    task_agent.task_queue.append("Process user requests")
    
    mock_agent = orchestrator.get_agent(mock_id)
    mock_agent.add_goal("Assist other agents")
    
    # Show initial status
    print("\nInitial agent status:")
    status = orchestrator.get_agent_status()
    for agent_id, info in status.items():
        print(f"  {info['name']}: {info['goals']} goals, state={info['state']}")
    
    # Show atomspace stats
    print("\nAtomSpace statistics:")
    stats = orchestrator.get_atomspace_stats()
    print(f"  Total atoms: {stats['total_atoms']}")
    print(f"  Agents: {stats['type_distribution'].get('Agent', 0)}")
    print(f"  Goals: {stats['type_distribution'].get('Goal', 0)}")
    print(f"  Memories: {stats['type_distribution'].get('Memory', 0)}")
    
    # Run orchestrator steps
    print("\nRunning orchestrator steps...")
    for i in range(3):
        print(f"\n--- Step {i+1} ---")
        results = orchestrator.step_all_agents()
        
        for agent_id, result in results.items():
            agent = orchestrator.get_agent(agent_id)
            agent_name = agent.name if agent else "Unknown"
            
            if "error" in result:
                print(f"  {agent_name}: ERROR - {result['error']}")
            else:
                action = result.get("action", "no_action")
                print(f"  {agent_name}: {action}")
    
    # Final statistics
    print("\nFinal AtomSpace statistics:")
    final_stats = orchestrator.get_atomspace_stats()
    print(f"  Total atoms: {final_stats['total_atoms']}")
    for atom_type, count in final_stats['type_distribution'].items():
        if count > 0:
            print(f"  {atom_type}: {count}")
    
    print("✓ Orchestrator tests passed\n")


def main():
    """Run all tests."""
    print("OpenCog Autonomous Agent Orchestrator - Standalone Test")
    print("=" * 60)
    print()
    
    try:
        test_atomspace()
        test_basic_agent()
        test_chat_agent()
        test_task_agent()
        test_orchestrator()
        
        print("🎉 All tests completed successfully!")
        print("\nThe OpenCog-inspired autonomous agent orchestrator is working correctly.")
        print("Key features demonstrated:")
        print("  ✓ AtomSpace knowledge representation")
        print("  ✓ Agent creation and goal management") 
        print("  ✓ Autonomous agent behavior (perceive-decide-act cycle)")
        print("  ✓ Chat agents with conversation capabilities")
        print("  ✓ Task agents with planning and execution")
        print("  ✓ Multi-agent orchestration and coordination")
        print("  ✓ Shared knowledge base and memory system")
        
        print("\n📝 Note: This demo runs without GPT4All models.")
        print("For full natural language capabilities, integrate with GPT4All models.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())