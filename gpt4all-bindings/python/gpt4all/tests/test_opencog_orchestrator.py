"""
Tests for OpenCog-inspired autonomous agent orchestrator.
"""
import pytest
import time
from unittest.mock import Mock, patch

from gpt4all.opencog_orchestrator import (
    AtomSpace, Atom, AtomType, Agent, ChatAgent, TaskAgent, 
    AgentOrchestrator, AgentState, Goal, create_example_orchestrator
)


class TestAtom:
    """Test the Atom class."""
    
    def test_atom_creation(self):
        """Test basic atom creation."""
        atom = Atom(
            atom_type=AtomType.CONCEPT,
            name="test_concept",
            value="test_value",
            confidence=0.8
        )
        
        assert atom.atom_type == AtomType.CONCEPT
        assert atom.name == "test_concept"
        assert atom.value == "test_value"
        assert atom.confidence == 0.8
        assert atom.truth_value == 1.0  # default
        assert len(atom.atom_id) > 0  # UUID generated
    
    def test_atom_auto_name(self):
        """Test automatic name generation from value."""
        atom = Atom(atom_type=AtomType.CONCEPT, value="auto_name")
        assert atom.name == "auto_name"


class TestAtomSpace:
    """Test the AtomSpace class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.atomspace = AtomSpace()
    
    def test_add_and_get_atom(self):
        """Test adding and retrieving atoms."""
        atom = Atom(
            atom_type=AtomType.CONCEPT,
            name="test_concept",
            value="test_value"
        )
        
        atom_id = self.atomspace.add_atom(atom)
        assert atom_id == atom.atom_id
        
        retrieved = self.atomspace.get_atom(atom_id)
        assert retrieved is not None
        assert retrieved.name == "test_concept"
        assert retrieved.value == "test_value"
    
    def test_find_atoms_by_name(self):
        """Test finding atoms by name."""
        atom1 = Atom(atom_type=AtomType.CONCEPT, name="test")
        atom2 = Atom(atom_type=AtomType.AGENT, name="test")
        atom3 = Atom(atom_type=AtomType.CONCEPT, name="other")
        
        self.atomspace.add_atom(atom1)
        self.atomspace.add_atom(atom2)
        self.atomspace.add_atom(atom3)
        
        found = self.atomspace.find_atoms_by_name("test")
        assert len(found) == 2
        
        found_names = [a.name for a in found]
        assert "test" in found_names
    
    def test_find_atoms_by_type(self):
        """Test finding atoms by type."""
        concept1 = Atom(atom_type=AtomType.CONCEPT, name="concept1")
        concept2 = Atom(atom_type=AtomType.CONCEPT, name="concept2")
        agent1 = Atom(atom_type=AtomType.AGENT, name="agent1")
        
        self.atomspace.add_atom(concept1)
        self.atomspace.add_atom(concept2)
        self.atomspace.add_atom(agent1)
        
        concepts = self.atomspace.find_atoms_by_type(AtomType.CONCEPT)
        assert len(concepts) == 2
        
        agents = self.atomspace.find_atoms_by_type(AtomType.AGENT)
        assert len(agents) == 1
    
    def test_create_link(self):
        """Test creating links between atoms."""
        atom1 = Atom(atom_type=AtomType.AGENT, name="agent1")
        atom2 = Atom(atom_type=AtomType.GOAL, name="goal1")
        
        id1 = self.atomspace.add_atom(atom1)
        id2 = self.atomspace.add_atom(atom2)
        
        self.atomspace.create_link(id1, id2, "has_goal")
        
        # Check that the link was created
        retrieved1 = self.atomspace.get_atom(id1)
        retrieved2 = self.atomspace.get_atom(id2)
        
        assert id2 in retrieved1.outgoing
        assert id1 in retrieved2.incoming
    
    def test_query(self):
        """Test pattern matching query."""
        atom1 = Atom(
            atom_type=AtomType.AGENT, 
            name="test_agent",
            metadata={"role": "assistant"}
        )
        atom2 = Atom(
            atom_type=AtomType.AGENT, 
            name="other_agent",
            metadata={"role": "user"}
        )
        atom3 = Atom(atom_type=AtomType.CONCEPT, name="test_concept")
        
        self.atomspace.add_atom(atom1)
        self.atomspace.add_atom(atom2)
        self.atomspace.add_atom(atom3)
        
        # Query by type
        results = self.atomspace.query({"type": AtomType.AGENT})
        assert len(results) == 2
        
        # Query by name
        results = self.atomspace.query({"name": "test_agent"})
        assert len(results) == 1
        assert results[0].name == "test_agent"
        
        # Query by metadata
        results = self.atomspace.query({"role": "assistant"})
        assert len(results) == 1
        assert results[0].metadata["role"] == "assistant"


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def perceive(self):
        return {"test": True}
    
    def decide(self, observations):
        if observations.get("test"):
            return "test_action"
        return None
    
    def act(self, action):
        return {"action": action, "result": "success"}


class TestAgent:
    """Test the Agent base class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.atomspace = AtomSpace()
        self.agent = MockAgent("test_id", "TestAgent", self.atomspace)
    
    def test_agent_creation(self):
        """Test agent creation and atomspace registration."""
        assert self.agent.agent_id == "test_id"
        assert self.agent.name == "TestAgent"
        assert self.agent.state == AgentState.IDLE
        
        # Check that agent was registered in atomspace
        agent_atoms = self.atomspace.find_atoms_by_type(AtomType.AGENT)
        assert len(agent_atoms) == 1
        assert agent_atoms[0].name == "Agent_TestAgent"
    
    def test_add_goal(self):
        """Test adding goals to agent."""
        goal = self.agent.add_goal("Test goal", priority=0.8)
        
        assert len(self.agent.goals) == 1
        assert self.agent.goals[0].description == "Test goal"
        assert self.agent.goals[0].priority == 0.8
        
        # Check goal was added to atomspace
        goal_atoms = self.atomspace.find_atoms_by_type(AtomType.GOAL)
        assert len(goal_atoms) == 1
    
    def test_remember(self):
        """Test memory functionality."""
        self.agent.remember("Test memory")
        
        assert len(self.agent.memory) == 1
        assert self.agent.memory[0] == "Test memory"
        
        # Check memory was added to atomspace
        memory_atoms = self.atomspace.find_atoms_by_type(AtomType.MEMORY)
        assert len(memory_atoms) == 1
    
    def test_step(self):
        """Test agent cognitive step."""
        result = self.agent.step()
        
        assert result["action"] == "test_action"
        assert result["result"] == "success"
        assert self.agent.state == AgentState.IDLE
    
    def test_think_with_gpt_no_model(self):
        """Test thinking without GPT4All model."""
        response = self.agent.think_with_gpt("test prompt")
        assert "Agent TestAgent thinking: test prompt" in response


class TestChatAgent:
    """Test the ChatAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.atomspace = AtomSpace()
        self.agent = ChatAgent("chat_id", "ChatBot", self.atomspace, None)
    
    def test_chat_agent_creation(self):
        """Test chat agent specific attributes."""
        assert len(self.agent.conversation_history) == 0
        assert self.agent.current_topic == ""
    
    def test_respond_to_message(self):
        """Test message response functionality."""
        response = self.agent.respond_to_message("Hello", "user")
        
        assert len(self.agent.conversation_history) == 2  # user message + agent response
        assert self.agent.conversation_history[0]["agent"] == "user"
        assert self.agent.conversation_history[0]["message"] == "Hello"
        assert self.agent.conversation_history[1]["agent"] == "ChatBot"
        assert isinstance(response, str)
    
    def test_perceive(self):
        """Test chat agent perception."""
        self.agent.add_goal("Test goal")
        observations = self.agent.perceive()
        
        assert "conversation_length" in observations
        assert "current_topic" in observations
        assert "goals" in observations
        assert len(observations["goals"]) == 1
    
    def test_decide_with_goals(self):
        """Test decision making with active goals."""
        self.agent.add_goal("Test conversation")
        observations = self.agent.perceive()
        action = self.agent.decide(observations)
        
        assert action is not None
        assert action.startswith("start_conversation_about:")
    
    def test_act_start_conversation(self):
        """Test starting a conversation action."""
        result = self.agent.act("start_conversation_about:AI and technology")
        
        assert result["action"] == "conversation_started"
        assert result["topic"] == "AI and technology"
        assert self.agent.current_topic == "AI and technology"
        assert len(self.agent.conversation_history) == 1


class TestTaskAgent:
    """Test the TaskAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.atomspace = AtomSpace()
        self.agent = TaskAgent("task_id", "TaskBot", self.atomspace, None)
    
    def test_task_agent_creation(self):
        """Test task agent specific attributes."""
        assert len(self.agent.task_queue) == 0
        assert len(self.agent.completed_tasks) == 0
    
    def test_perceive(self):
        """Test task agent perception."""
        self.agent.task_queue.append("test task")
        self.agent.completed_tasks.append("done task")
        self.agent.add_goal("Test goal")
        
        observations = self.agent.perceive()
        
        assert observations["pending_tasks"] == 1
        assert observations["completed_tasks"] == 1
        assert observations["active_goals"] == 1
    
    def test_decide_with_tasks(self):
        """Test decision making with pending tasks."""
        self.agent.task_queue.append("urgent task")
        observations = self.agent.perceive()
        action = self.agent.decide(observations)
        
        assert action == "execute_task:urgent task"
    
    def test_decide_with_goals(self):
        """Test decision making with goals but no tasks."""
        self.agent.add_goal("Complete project")
        observations = self.agent.perceive()
        action = self.agent.decide(observations)
        
        assert action == "plan_for_goal:Complete project"
    
    def test_act_execute_task(self):
        """Test task execution action."""
        self.agent.task_queue.append("test task")
        result = self.agent.act("execute_task:test task")
        
        assert result["action"] == "task_completed"
        assert result["task"] == "test task"
        assert "test task" not in self.agent.task_queue
        assert "test task" in self.agent.completed_tasks


class TestAgentOrchestrator:
    """Test the AgentOrchestrator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = AgentOrchestrator(max_agents=3)
    
    def test_orchestrator_creation(self):
        """Test orchestrator initialization."""
        assert len(self.orchestrator.agents) == 0
        assert self.orchestrator.max_agents == 3
        assert isinstance(self.orchestrator.atomspace, AtomSpace)
    
    def test_create_agent(self):
        """Test agent creation through orchestrator."""
        agent_id = self.orchestrator.create_agent(ChatAgent, "TestChat", None)
        
        assert len(self.orchestrator.agents) == 1
        assert agent_id in self.orchestrator.agents
        
        agent = self.orchestrator.get_agent(agent_id)
        assert agent is not None
        assert agent.name == "TestChat"
        assert isinstance(agent, ChatAgent)
    
    def test_max_agents_limit(self):
        """Test maximum agents limit."""
        # Create max number of agents
        for i in range(3):
            self.orchestrator.create_agent(MockAgent, f"Agent{i}", None)
        
        # Try to create one more - should fail
        with pytest.raises(ValueError, match="Maximum number of agents"):
            self.orchestrator.create_agent(MockAgent, "ExtraAgent", None)
    
    def test_remove_agent(self):
        """Test agent removal."""
        agent_id = self.orchestrator.create_agent(ChatAgent, "ToRemove", None)
        assert len(self.orchestrator.agents) == 1
        
        success = self.orchestrator.remove_agent(agent_id)
        assert success
        assert len(self.orchestrator.agents) == 0
        
        # Try to remove non-existent agent
        success = self.orchestrator.remove_agent("non_existent")
        assert not success
    
    def test_step_agent(self):
        """Test stepping individual agent."""
        agent_id = self.orchestrator.create_agent(MockAgent, "TestAgent", None)
        result = self.orchestrator.step_agent(agent_id)
        
        assert "action" in result
        assert result["action"] == "test_action"
    
    def test_step_all_agents(self):
        """Test stepping all agents."""
        agent_id1 = self.orchestrator.create_agent(MockAgent, "Agent1", None)
        agent_id2 = self.orchestrator.create_agent(ChatAgent, "Agent2", None)
        
        results = self.orchestrator.step_all_agents()
        
        assert len(results) == 2
        assert agent_id1 in results
        assert agent_id2 in results
    
    def test_get_agent_status(self):
        """Test getting agent status."""
        agent_id = self.orchestrator.create_agent(ChatAgent, "StatusTest", None)
        agent = self.orchestrator.get_agent(agent_id)
        agent.add_goal("Test goal")
        
        status = self.orchestrator.get_agent_status()
        
        assert len(status) == 1
        assert agent_id in status
        
        agent_status = status[agent_id]
        assert agent_status["name"] == "StatusTest"
        assert agent_status["state"] == "idle"
        assert agent_status["goals"] == 1
    
    def test_get_atomspace_stats(self):
        """Test getting atomspace statistics."""
        # Create some agents to populate atomspace
        self.orchestrator.create_agent(ChatAgent, "Chat", None)
        self.orchestrator.create_agent(TaskAgent, "Task", None)
        
        stats = self.orchestrator.get_atomspace_stats()
        
        assert "total_atoms" in stats
        assert "type_distribution" in stats
        assert stats["total_atoms"] > 0
        assert stats["type_distribution"]["Agent"] == 2
    
    def test_running_context(self):
        """Test running context manager."""
        assert not self.orchestrator.running
        
        with self.orchestrator.running_context():
            assert self.orchestrator.running
        
        assert not self.orchestrator.running


class TestCreateExampleOrchestrator:
    """Test the create_example_orchestrator function."""
    
    @patch('gpt4all.opencog_orchestrator.GPT4All')
    def test_create_with_mock_gpt4all(self, mock_gpt4all):
        """Test creating orchestrator with mocked GPT4All."""
        mock_model = Mock()
        mock_gpt4all.return_value = mock_model
        
        orchestrator = create_example_orchestrator("test-model")
        
        assert len(orchestrator.agents) == 2
        agents = list(orchestrator.agents.values())
        
        # Check that we have the expected agent types
        agent_types = [type(agent).__name__ for agent in agents]
        assert "ChatAgent" in agent_types
        assert "TaskAgent" in agent_types
        
        # Check that agents have goals
        for agent in agents:
            assert len(agent.goals) > 0
    
    def test_create_without_gpt4all(self):
        """Test creating orchestrator when GPT4All is not available."""
        # This should not raise an exception
        orchestrator = create_example_orchestrator("non-existent-model")
        
        # Should still create agents, but without GPT4All models
        assert len(orchestrator.agents) == 2
    

def test_goal_class():
    """Test the Goal class."""
    goal = Goal(description="Test goal", priority=0.8)
    
    assert goal.description == "Test goal"
    assert goal.priority == 0.8
    assert not goal.completed
    assert goal.progress == 0.0
    assert len(goal.goal_id) > 0