"""
OpenCog-inspired autonomous user agent orchestrator for GPT4All.

This module implements core OpenCog concepts like AtomSpace and cognitive architecture
to orchestrate autonomous agents that can interact with GPT4All models.
"""
from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, Future
import threading
from contextlib import contextmanager

try:
    from .gpt4all import GPT4All
except ImportError:
    # GPT4All not available - create a dummy class for typing
    class GPT4All:
        def __init__(self, *args, **kwargs):
            raise ImportError("GPT4All not available")
        def generate(self, *args, **kwargs):
            return "GPT4All not available"


class AtomType(Enum):
    """Types of atoms in our simplified AtomSpace."""
    CONCEPT = "Concept"
    PREDICATE = "Predicate" 
    EVALUATION = "Evaluation"
    LIST = "List"
    AGENT = "Agent"
    GOAL = "Goal"
    MEMORY = "Memory"
    ACTION = "Action"


@dataclass
class Atom:
    """
    Simplified Atom representation inspired by OpenCog AtomSpace.
    
    Atoms are the basic building blocks of knowledge in the cognitive architecture.
    """
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    atom_type: AtomType = AtomType.CONCEPT
    name: str = ""
    value: Any = None
    confidence: float = 1.0
    truth_value: float = 1.0
    incoming: Set[str] = field(default_factory=set)
    outgoing: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.name and self.value:
            self.name = str(self.value)


class AtomSpace:
    """
    Simplified AtomSpace implementation for knowledge representation and management.
    
    The AtomSpace is the central knowledge database that stores all atoms and their
    relationships in a graph structure.
    """
    
    def __init__(self):
        self._atoms: Dict[str, Atom] = {}
        self._name_index: Dict[str, Set[str]] = {}
        self._type_index: Dict[AtomType, Set[str]] = {}
        self._lock = threading.RLock()
    
    def add_atom(self, atom: Atom) -> str:
        """Add an atom to the AtomSpace."""
        with self._lock:
            self._atoms[atom.atom_id] = atom
            
            # Update indices
            if atom.name:
                if atom.name not in self._name_index:
                    self._name_index[atom.name] = set()
                self._name_index[atom.name].add(atom.atom_id)
            
            if atom.atom_type not in self._type_index:
                self._type_index[atom.atom_type] = set()
            self._type_index[atom.atom_type].add(atom.atom_id)
            
            return atom.atom_id
    
    def get_atom(self, atom_id: str) -> Optional[Atom]:
        """Get an atom by ID."""
        return self._atoms.get(atom_id)
    
    def find_atoms_by_name(self, name: str) -> List[Atom]:
        """Find atoms by name."""
        atom_ids = self._name_index.get(name, set())
        return [self._atoms[aid] for aid in atom_ids]
    
    def find_atoms_by_type(self, atom_type: AtomType) -> List[Atom]:
        """Find atoms by type."""
        atom_ids = self._type_index.get(atom_type, set())
        return [self._atoms[aid] for aid in atom_ids]
    
    def create_link(self, from_atom: str, to_atom: str, link_type: str = "link"):
        """Create a link between two atoms."""
        with self._lock:
            if from_atom in self._atoms and to_atom in self._atoms:
                self._atoms[from_atom].outgoing.append(to_atom)
                self._atoms[to_atom].incoming.add(from_atom)
    
    def query(self, pattern: Dict[str, Any]) -> List[Atom]:
        """Simple pattern matching query."""
        results = []
        for atom in self._atoms.values():
            match = True
            for key, value in pattern.items():
                if key == "type" and atom.atom_type != value:
                    match = False
                    break
                elif key == "name" and atom.name != value:
                    match = False
                    break
                elif key in atom.metadata and atom.metadata[key] != value:
                    match = False
                    break
            if match:
                results.append(atom)
        return results


class AgentState(Enum):
    """States an agent can be in."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class Goal:
    """Represents an agent's goal."""
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: float = 1.0
    deadline: Optional[float] = None
    completed: bool = False
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """
    Base class for autonomous agents in the OpenCog-inspired system.
    
    Agents can perceive, think, and act in their environment using GPT4All models
    for natural language processing and generation.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 atomspace: AtomSpace,
                 gpt4all_model: Optional[GPT4All] = None):
        self.agent_id = agent_id
        self.name = name
        self.atomspace = atomspace
        self.gpt4all = gpt4all_model
        self.state = AgentState.IDLE
        self.goals: List[Goal] = []
        self.memory: List[str] = []
        self.context: Dict[str, Any] = {}
        self.last_action_time = time.time()
        
        # Register self in atomspace
        agent_atom = Atom(
            atom_type=AtomType.AGENT,
            name=f"Agent_{name}",
            value=self.agent_id,
            metadata={"agent_type": self.__class__.__name__}
        )
        self.atomspace.add_atom(agent_atom)
    
    def add_goal(self, description: str, priority: float = 1.0) -> Goal:
        """Add a new goal for the agent."""
        goal = Goal(description=description, priority=priority)
        self.goals.append(goal)
        
        # Store goal in atomspace
        goal_atom = Atom(
            atom_type=AtomType.GOAL,
            name=f"Goal_{goal.goal_id}",
            value=description,
            metadata={"agent_id": self.agent_id, "priority": priority}
        )
        self.atomspace.add_atom(goal_atom)
        return goal
    
    def remember(self, memory: str):
        """Store a memory."""
        self.memory.append(memory)
        memory_atom = Atom(
            atom_type=AtomType.MEMORY,
            name=f"Memory_{len(self.memory)}",
            value=memory,
            metadata={"agent_id": self.agent_id, "timestamp": time.time()}
        )
        self.atomspace.add_atom(memory_atom)
    
    def think_with_gpt(self, prompt: str, max_tokens: int = 200) -> str:
        """Use GPT4All to process thoughts."""
        if not self.gpt4all:
            return f"Agent {self.name} thinking: {prompt}"
        
        self.state = AgentState.THINKING
        try:
            with self.gpt4all.chat_session():
                response = self.gpt4all.generate(
                    f"As agent {self.name}, {prompt}",
                    max_tokens=max_tokens
                )
            self.state = AgentState.IDLE
            return response
        except Exception as e:
            self.state = AgentState.ERROR
            return f"Error thinking: {e}"
    
    @abstractmethod
    def perceive(self) -> Dict[str, Any]:
        """Perceive the environment and return observations."""
        pass
    
    @abstractmethod
    def decide(self, observations: Dict[str, Any]) -> Optional[str]:
        """Decide what action to take based on observations."""
        pass
    
    @abstractmethod
    def act(self, action: str) -> Dict[str, Any]:
        """Execute an action and return results."""
        pass
    
    def step(self) -> Dict[str, Any]:
        """Execute one cognitive step: perceive -> decide -> act."""
        observations = self.perceive()
        action = self.decide(observations)
        
        if action:
            self.state = AgentState.ACTING
            results = self.act(action)
            self.state = AgentState.IDLE
            self.last_action_time = time.time()
            return results
        
        return {"status": "no_action", "observations": observations}


class ChatAgent(Agent):
    """
    A conversational agent that can engage in dialogue using GPT4All.
    """
    
    def __init__(self, agent_id: str, name: str, atomspace: AtomSpace, gpt4all_model: GPT4All):
        super().__init__(agent_id, name, atomspace, gpt4all_model)
        self.conversation_history: List[Dict[str, str]] = []
        self.current_topic = ""
    
    def perceive(self) -> Dict[str, Any]:
        """Perceive incoming messages or conversation state."""
        return {
            "conversation_length": len(self.conversation_history),
            "current_topic": self.current_topic,
            "goals": [g.description for g in self.goals if not g.completed]
        }
    
    def decide(self, observations: Dict[str, Any]) -> Optional[str]:
        """Decide whether to initiate conversation or respond."""
        if self.goals and not self.current_topic:
            active_goals = [g for g in self.goals if not g.completed]
            if active_goals:
                return f"start_conversation_about:{active_goals[0].description}"
        return None
    
    def act(self, action: str) -> Dict[str, Any]:
        """Execute conversational action."""
        if action.startswith("start_conversation_about:"):
            topic = action.split(":", 1)[1]
            self.current_topic = topic
            
            response = self.think_with_gpt(
                f"Start a conversation about: {topic}. "
                f"Introduce yourself as {self.name} and explain your interest in this topic."
            )
            
            self.conversation_history.append({
                "agent": self.name,
                "message": response,
                "timestamp": time.time()
            })
            
            self.remember(f"Started conversation about {topic}")
            return {"action": "conversation_started", "response": response, "topic": topic}
        
        return {"action": "unknown", "result": "Action not recognized"}
    
    def respond_to_message(self, message: str, sender: str = "user") -> str:
        """Respond to an incoming message."""
        self.conversation_history.append({
            "agent": sender,
            "message": message,
            "timestamp": time.time()
        })
        
        context = f"Previous conversation: {self.conversation_history[-3:]}" if len(self.conversation_history) > 1 else ""
        response = self.think_with_gpt(
            f"{context}\n\nRespond to this message: '{message}'"
        )
        
        self.conversation_history.append({
            "agent": self.name,
            "message": response,
            "timestamp": time.time()
        })
        
        return response


class TaskAgent(Agent):
    """
    An agent focused on completing specific tasks using GPT4All reasoning.
    """
    
    def __init__(self, agent_id: str, name: str, atomspace: AtomSpace, gpt4all_model: GPT4All):
        super().__init__(agent_id, name, atomspace, gpt4all_model)
        self.task_queue: List[str] = []
        self.completed_tasks: List[str] = []
    
    def perceive(self) -> Dict[str, Any]:
        """Perceive current task state and goals."""
        return {
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "active_goals": len([g for g in self.goals if not g.completed])
        }
    
    def decide(self, observations: Dict[str, Any]) -> Optional[str]:
        """Decide on next task or goal to work on."""
        if self.task_queue:
            return f"execute_task:{self.task_queue[0]}"
        
        # Look for incomplete goals and create tasks
        for goal in self.goals:
            if not goal.completed:
                return f"plan_for_goal:{goal.description}"
        
        return None
    
    def act(self, action: str) -> Dict[str, Any]:
        """Execute task-related actions."""
        if action.startswith("execute_task:"):
            task = action.split(":", 1)[1]
            self.task_queue.remove(task)
            
            # Use GPT to work on the task
            result = self.think_with_gpt(
                f"Work on this task: {task}. "
                f"Provide a detailed plan or solution."
            )
            
            self.completed_tasks.append(task)
            self.remember(f"Completed task: {task}")
            
            return {"action": "task_completed", "task": task, "result": result}
        
        elif action.startswith("plan_for_goal:"):
            goal_desc = action.split(":", 1)[1]
            
            # Use GPT to break down the goal into tasks
            plan = self.think_with_gpt(
                f"Break down this goal into specific, actionable tasks: {goal_desc}"
            )
            
            # Extract tasks from the plan (simplified)
            task_lines = [line.strip() for line in plan.split('\n') if line.strip() and ('task' in line.lower() or line.strip().startswith('-'))]
            for task_line in task_lines[:3]:  # Limit to 3 tasks
                clean_task = task_line.replace('-', '').replace('Task:', '').strip()
                if clean_task:
                    self.task_queue.append(clean_task)
            
            return {"action": "goal_planned", "goal": goal_desc, "tasks_created": len(task_lines)}
        
        return {"action": "unknown", "result": "Action not recognized"}


class AgentOrchestrator:
    """
    OpenCog-inspired orchestrator for managing multiple autonomous agents.
    
    The orchestrator coordinates agent interactions, manages the shared AtomSpace,
    and handles agent lifecycle and communication.
    """
    
    def __init__(self, max_agents: int = 10):
        self.atomspace = AtomSpace()
        self.agents: Dict[str, Agent] = {}
        self.max_agents = max_agents
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=max_agents)
        self.agent_futures: Dict[str, Future] = {}
        self._lock = threading.RLock()
    
    def create_agent(self, 
                     agent_class: type, 
                     name: str, 
                     gpt4all_model: Optional[GPT4All] = None,
                     **kwargs) -> str:
        """Create and register a new agent."""
        if len(self.agents) >= self.max_agents:
            raise ValueError(f"Maximum number of agents ({self.max_agents}) reached")
        
        agent_id = str(uuid.uuid4())
        agent = agent_class(agent_id, name, self.atomspace, gpt4all_model, **kwargs)
        
        with self._lock:
            self.agents[agent_id] = agent
        
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the orchestrator."""
        with self._lock:
            if agent_id in self.agents:
                # Cancel any running future
                if agent_id in self.agent_futures:
                    self.agent_futures[agent_id].cancel()
                    del self.agent_futures[agent_id]
                
                del self.agents[agent_id]
                return True
        return False
    
    def step_agent(self, agent_id: str) -> Dict[str, Any]:
        """Execute one step for a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}
        
        try:
            return agent.step()
        except Exception as e:
            return {"error": str(e), "agent_id": agent_id}
    
    def step_all_agents(self) -> Dict[str, Any]:
        """Execute one step for all agents."""
        results = {}
        
        with self._lock:
            agent_ids = list(self.agents.keys())
        
        for agent_id in agent_ids:
            results[agent_id] = self.step_agent(agent_id)
        
        return results
    
    @contextmanager
    def running_context(self):
        """Context manager for running the orchestrator."""
        self.running = True
        try:
            yield self
        finally:
            self.running = False
            # Cancel all futures
            for future in self.agent_futures.values():
                future.cancel()
            self.agent_futures.clear()
    
    def run_continuous(self, step_interval: float = 1.0, max_steps: Optional[int] = None):
        """Run agents continuously in a loop."""
        step_count = 0
        
        with self.running_context():
            while self.running and (max_steps is None or step_count < max_steps):
                start_time = time.time()
                
                # Step all agents
                results = self.step_all_agents()
                
                # Log results (simplified)
                active_agents = sum(1 for r in results.values() if not r.get("error"))
                
                step_count += 1
                elapsed = time.time() - start_time
                
                # Sleep to maintain interval
                if elapsed < step_interval:
                    time.sleep(step_interval - elapsed)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "name": agent.name,
                "state": agent.state.value,
                "goals": len(agent.goals),
                "memories": len(agent.memory),
                "last_action": agent.last_action_time
            }
        return status
    
    def get_atomspace_stats(self) -> Dict[str, Any]:
        """Get statistics about the AtomSpace."""
        type_counts = {}
        for atom_type in AtomType:
            atoms = self.atomspace.find_atoms_by_type(atom_type)
            type_counts[atom_type.value] = len(atoms)
        
        return {
            "total_atoms": len(self.atomspace._atoms),
            "type_distribution": type_counts,
            "indexed_names": len(self.atomspace._name_index)
        }


def create_example_orchestrator(model_name: str = "orca-mini-3b-gguf2-q4_0.gguf") -> AgentOrchestrator:
    """
    Create an example orchestrator with some pre-configured agents.
    
    Args:
        model_name: Name of the GPT4All model to use for agents
        
    Returns:
        Configured AgentOrchestrator instance
    """
    orchestrator = AgentOrchestrator(max_agents=5)
    
    try:
        # Try to create a GPT4All model (will fail if model not available)
        gpt4all_model = GPT4All(model_name, allow_download=False)
        
        # Create example agents
        chat_agent_id = orchestrator.create_agent(
            ChatAgent, 
            "ChatBot", 
            gpt4all_model
        )
        chat_agent = orchestrator.get_agent(chat_agent_id)
        chat_agent.add_goal("Engage users in meaningful conversations")
        chat_agent.add_goal("Learn about user preferences and interests")
        
        task_agent_id = orchestrator.create_agent(
            TaskAgent, 
            "TaskManager", 
            gpt4all_model
        )
        task_agent = orchestrator.get_agent(task_agent_id)
        task_agent.add_goal("Complete user-assigned tasks efficiently")
        task_agent.add_goal("Provide helpful solutions and recommendations")
        
    except Exception as e:
        # If GPT4All model is not available, create agents without it
        print(f"Could not load GPT4All model: {e}")
        print("Creating agents without GPT4All model (limited functionality)")
        
        orchestrator.create_agent(ChatAgent, "ChatBot", None)
        orchestrator.create_agent(TaskAgent, "TaskManager", None)
    
    return orchestrator