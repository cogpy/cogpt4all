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
import math
import random

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
    BOOTSTRAP = "Bootstrap"
    HOMEOSTATIC_STATE = "HomeostaticState"
    INFERENCE_VORTEX = "InferenceVortex"
    FEEDBACK_LOOP = "FeedbackLoop"
    AUTOPOIETIC_PROCESS = "AutopoieticProcess"
    METACOGNITIVE_REFLECTION = "MetacognitiveReflection"


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


@dataclass
class HomeostaticState:
    """Represents homeostatic state for entropy resistance."""
    agent_id: str = ""
    entropy_level: float = 0.0
    coherence_score: float = 1.0
    stability_index: float = 1.0
    last_update: float = field(default_factory=time.time)
    
    def update_entropy(self, action_variance: float, memory_coherence: float):
        """Update entropy based on agent actions and memory coherence."""
        # Higher variance increases entropy, coherent memory reduces it
        entropy_delta = action_variance * 0.1 - memory_coherence * 0.05
        self.entropy_level = max(0.0, min(1.0, self.entropy_level + entropy_delta))
        
        # Update stability and coherence inversely related to entropy
        self.stability_index = 1.0 - self.entropy_level
        self.coherence_score = max(0.1, self.coherence_score - entropy_delta * 0.5)
        self.last_update = time.time()
    
    def needs_bootstrap(self) -> bool:
        """Determine if agent needs bootstrap intervention."""
        return self.entropy_level > 0.7 or self.coherence_score < 0.3


@dataclass 
class BootstrapMechanism:
    """Foundational bootstrap mechanisms to combat entropic drift."""
    target_agent_id: str = ""
    bootstrap_type: str = "coherence_restoration"
    activation_threshold: float = 0.7
    intervention_strength: float = 0.5
    last_activation: float = 0.0
    
    def should_activate(self, homeostatic_state: HomeostaticState) -> bool:
        """Check if bootstrap mechanism should activate."""
        if self.bootstrap_type == "coherence_restoration":
            return homeostatic_state.coherence_score < self.activation_threshold
        elif self.bootstrap_type == "entropy_regulation":
            return homeostatic_state.entropy_level > self.activation_threshold
        elif self.bootstrap_type == "stability_maintenance":
            return homeostatic_state.stability_index < self.activation_threshold
        return False
    
    def apply_intervention(self, agent) -> Dict[str, Any]:
        """Apply bootstrap intervention to agent."""
        self.last_activation = time.time()
        
        if self.bootstrap_type == "coherence_restoration":
            # Reorganize agent's goals and memories for better coherence
            agent.reorganize_cognitive_structures()
            return {"intervention": "coherence_restored", "strength": self.intervention_strength}
            
        elif self.bootstrap_type == "entropy_regulation":
            # Reset high-entropy patterns and establish order
            agent.regulate_entropy()
            return {"intervention": "entropy_regulated", "strength": self.intervention_strength}
            
        elif self.bootstrap_type == "stability_maintenance":
            # Reinforce stable behavioral patterns
            agent.reinforce_stability()
            return {"intervention": "stability_reinforced", "strength": self.intervention_strength}
        
        return {"intervention": "unknown", "strength": 0.0}


class Agent(ABC):
    """
    Base class for autonomous agents in the OpenCog-inspired system.
    
    Agents can perceive, think, and act in their environment using GPT4All models
    for natural language processing and generation. Enhanced with homeostatic
    regulation and bootstrap mechanisms to resist entropic drift.
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
        
        # Homeostatic and bootstrap systems
        self.homeostatic_state = HomeostaticState(agent_id=agent_id)
        self.bootstrap_mechanisms: List[BootstrapMechanism] = [
            BootstrapMechanism(agent_id, "coherence_restoration", 0.3, 0.7),
            BootstrapMechanism(agent_id, "entropy_regulation", 0.7, 0.6),
            BootstrapMechanism(agent_id, "stability_maintenance", 0.4, 0.5)
        ]
        self.action_history: List[str] = []
        self.cognitive_variance = 0.0
        
        # Advanced cognitive systems
        self.inference_vortex = InferenceVortex(agent_id=agent_id)
        self.agentic_event_loop = AgenticEventLoop(agent_id=agent_id)
        self.agentic_event_loop.add_vortex(self.inference_vortex)
        
        # Virtual engine for feedback loops and training
        self.virtual_engine = VirtualEngine(agent_id=agent_id)
        
        # Autopoietic processes for self-maintenance
        self.autopoietic_process = AutopoieticProcess(agent_id=agent_id, process_type="self_maintenance")
        
        # Start initial training session
        self.current_training_session = self.virtual_engine.start_training_session("adaptive")
        
        # Register self in atomspace
        agent_atom = Atom(
            atom_type=AtomType.AGENT,
            name=f"Agent_{name}",
            value=self.agent_id,
            metadata={"agent_type": self.__class__.__name__}
        )
        self.atomspace.add_atom(agent_atom)
        
        # Initialize homeostatic state in atomspace
        homeostatic_atom = Atom(
            atom_type=AtomType.HOMEOSTATIC_STATE,
            name=f"HomeostaticState_{agent_id}",
            value=self.homeostatic_state,
            metadata={"agent_id": agent_id}
        )
        self.atomspace.add_atom(homeostatic_atom)
    
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
    
    def reorganize_cognitive_structures(self):
        """Reorganize goals and memories for better coherence."""
        # Sort goals by priority and relevance
        self.goals.sort(key=lambda g: (g.priority, -g.progress), reverse=True)
        
        # Consolidate related memories
        if len(self.memory) > 10:
            # Keep most recent and important memories
            important_memories = self.memory[-5:]  # Recent memories
            self.memory = important_memories
        
        # Update homeostatic state
        coherence_improvement = 0.2
        self.homeostatic_state.coherence_score = min(1.0, 
            self.homeostatic_state.coherence_score + coherence_improvement)
        
        self.remember(f"Reorganized cognitive structures - coherence improved")
    
    def regulate_entropy(self):
        """Regulate entropy by establishing predictable patterns."""
        # Reset high-variance behaviors
        self.cognitive_variance *= 0.5
        
        # Establish regular patterns
        if not self.goals:
            self.add_goal("Maintain cognitive stability", priority=0.9)
        
        # Reduce entropy level
        entropy_reduction = 0.3
        self.homeostatic_state.entropy_level = max(0.0,
            self.homeostatic_state.entropy_level - entropy_reduction)
        
        self.remember(f"Regulated entropy - variance reduced")
    
    def reinforce_stability(self):
        """Reinforce stable behavioral patterns."""
        # Increase priority of completed goals to reinforce success patterns
        for goal in self.goals:
            if goal.completed:
                goal.priority = min(1.0, goal.priority + 0.1)
        
        # Improve stability index
        stability_improvement = 0.25
        self.homeostatic_state.stability_index = min(1.0,
            self.homeostatic_state.stability_index + stability_improvement)
        
        self.remember(f"Reinforced stability patterns")
    
    def update_homeostatic_state(self, action: str):
        """Update homeostatic state based on recent actions."""
        self.action_history.append(action)
        
        # Keep limited action history
        if len(self.action_history) > 20:
            self.action_history = self.action_history[-15:]
        
        # Calculate action variance (consistency measure)
        if len(self.action_history) >= 3:
            action_types = [a.split(":")[0] if ":" in a else a for a in self.action_history[-5:]]
            unique_actions = len(set(action_types))
            total_actions = len(action_types)
            variance = unique_actions / total_actions if total_actions > 0 else 0
            self.cognitive_variance = variance
        
        # Calculate memory coherence
        memory_coherence = 1.0
        if len(self.memory) > 5:
            # Simple coherence based on memory length stability
            memory_coherence = min(1.0, 10.0 / len(self.memory))
        
        # Update homeostatic state
        self.homeostatic_state.update_entropy(self.cognitive_variance, memory_coherence)
    
    def check_bootstrap_interventions(self) -> List[Dict[str, Any]]:
        """Check and apply bootstrap interventions if needed."""
        interventions = []
        
        for mechanism in self.bootstrap_mechanisms:
            if mechanism.should_activate(self.homeostatic_state):
                # Apply intervention
                result = mechanism.apply_intervention(self)
                interventions.append(result)
                
                # Log bootstrap intervention in atomspace
                bootstrap_atom = Atom(
                    atom_type=AtomType.BOOTSTRAP,
                    name=f"Bootstrap_{mechanism.bootstrap_type}_{self.agent_id}",
                    value=result,
                    metadata={
                        "agent_id": self.agent_id,
                        "mechanism_type": mechanism.bootstrap_type,
                        "timestamp": time.time()
                    }
                )
                self.atomspace.add_atom(bootstrap_atom)
        
        return interventions
    
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
        """Execute one cognitive step: perceive -> decide -> act with homeostatic monitoring."""
        observations = self.perceive()
        
        # Process observations through inference vortex
        self.agentic_event_loop.queue_event("perception", observations)
        vortex_cycle = self.agentic_event_loop.process_cycle()
        
        # Extract enhanced observations from vortex processing
        enhanced_observations = observations
        if vortex_cycle["vortex_outputs"]:
            # Use the most recent vortex output for decision making
            latest_output = vortex_cycle["vortex_outputs"][-1]["output"]
            enhanced_observations = {**observations, **latest_output}
        
        action = self.decide(enhanced_observations)
        
        result = {"status": "no_action", "observations": observations}
        
        if action:
            self.state = AgentState.ACTING
            action_results = self.act(action)
            self.state = AgentState.IDLE
            self.last_action_time = time.time()
            
            # Update homeostatic state based on action
            self.update_homeostatic_state(action)
            
            # Process homeostatic measurements through virtual engine
            measurements = {
                "coherence": self.homeostatic_state.coherence_score,
                "stability": self.homeostatic_state.stability_index,
                "entropy": self.homeostatic_state.entropy_level,
                "learning_rate": self.cognitive_variance
            }
            
            control_outputs = self.virtual_engine.update_measurements(measurements)
            
            # Apply control outputs to adjust agent behavior
            self._apply_feedback_controls(control_outputs)
            
            # Execute autopoietic cycle for self-maintenance
            autopoietic_cycle = self.autopoietic_process.execute_autopoietic_cycle()
            
            # Store autopoietic data in atomspace
            autopoietic_atom = Atom(
                atom_type=AtomType.AUTOPOIETIC_PROCESS,
                name=f"AutopoieticCycle_{self.agent_id}_{int(time.time())}",
                value=autopoietic_cycle,
                metadata={
                    "agent_id": self.agent_id,
                    "emergence_stage": self.autopoietic_process.emergence_stage,
                    "closure_achieved": self.autopoietic_process.closure_achieved
                }
            )
            self.atomspace.add_atom(autopoietic_atom)
            
            # Check for bootstrap interventions
            interventions = self.check_bootstrap_interventions()
            
            result = {
                **action_results,
                "homeostatic_state": {
                    "entropy": self.homeostatic_state.entropy_level,
                    "coherence": self.homeostatic_state.coherence_score,
                    "stability": self.homeostatic_state.stability_index
                },
                "bootstrap_interventions": interventions,
                "vortex_cycle": vortex_cycle,
                "inference_vortex_state": self.inference_vortex.get_vortex_state(),
                "event_loop_state": self.agentic_event_loop.get_loop_status(),
                "virtual_engine_status": self.virtual_engine.get_engine_status(),
                "feedback_controls": control_outputs,
                "autopoietic_cycle": autopoietic_cycle,
                "autopoietic_status": self.autopoietic_process.get_autopoietic_status()
            }
        
        return result
    
    def _apply_feedback_controls(self, control_outputs: Dict[str, float]):
        """Apply feedback control outputs to adjust agent behavior."""
        for control_name, control_value in control_outputs.items():
            if control_name == "coherence":
                # Positive control value improves coherence
                if control_value > 0:
                    self.homeostatic_state.coherence_score = min(1.0, 
                        self.homeostatic_state.coherence_score + control_value * 0.01)
                    
            elif control_name == "stability":
                # Positive control value improves stability
                if control_value > 0:
                    self.homeostatic_state.stability_index = min(1.0,
                        self.homeostatic_state.stability_index + control_value * 0.01)
                    
            elif control_name == "entropy":
                # Positive control value reduces entropy (entropy target is low)
                if control_value > 0:
                    self.homeostatic_state.entropy_level = max(0.0,
                        self.homeostatic_state.entropy_level - control_value * 0.01)
                    
            elif control_name == "learning_rate":
                # Adjust cognitive variance (learning rate)
                if control_value > 0:
                    self.cognitive_variance = min(1.0, self.cognitive_variance + control_value * 0.005)
                else:
                    self.cognitive_variance = max(0.0, self.cognitive_variance + control_value * 0.005)
        
        # Store feedback loop data in atomspace
        feedback_atom = Atom(
            atom_type=AtomType.FEEDBACK_LOOP,
            name=f"FeedbackControl_{self.agent_id}_{int(time.time())}",
            value=control_outputs,
            metadata={
                "agent_id": self.agent_id,
                "timestamp": time.time(),
                "equilibrium_achieved": self.virtual_engine.equilibrium_state
            }
        )
        self.atomspace.add_atom(feedback_atom)


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
            
        return {"action": "unknown", "result": "Action not recognized"}


@dataclass
class InferenceVortex:
    """
    Inference engine vortex for dynamic knowledge transformation.
    
    Creates spiraling patterns of inference that transform raw observations
    into increasingly refined knowledge through metamorphic processes.
    """
    vortex_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    intensity: float = 1.0
    rotation_direction: str = "clockwise"  # or "counterclockwise"
    transformation_layers: List[str] = field(default_factory=list)
    knowledge_spiral: List[Dict[str, Any]] = field(default_factory=list)
    metamorphosis_stage: int = 0
    
    def __post_init__(self):
        if not self.transformation_layers:
            self.transformation_layers = [
                "raw_perception",
                "pattern_recognition", 
                "conceptual_abstraction",
                "relational_inference",
                "meta_knowledge_synthesis"
            ]
    
    def process_through_vortex(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through the inference vortex layers."""
        current_data = input_data
        transformation_path = []
        
        for layer_idx, layer in enumerate(self.transformation_layers):
            # Apply vortex transformation based on intensity and direction
            spiral_position = layer_idx * self.intensity
            if self.rotation_direction == "counterclockwise":
                spiral_position *= -1
            
            # Transform data through current layer
            transformed = self._apply_layer_transformation(layer, current_data, spiral_position)
            
            transformation_path.append({
                "layer": layer,
                "input": current_data,
                "output": transformed,
                "spiral_position": spiral_position
            })
            
            current_data = transformed
        
        # Store in knowledge spiral
        self.knowledge_spiral.append({
            "timestamp": time.time(),
            "transformation_path": transformation_path,
            "final_output": current_data,
            "metamorphosis_stage": self.metamorphosis_stage
        })
        
        # Increment metamorphosis stage
        self.metamorphosis_stage += 1
        if self.metamorphosis_stage >= len(self.transformation_layers):
            self.metamorphosis_stage = 0  # Reset for new cycle
        
        return current_data
    
    def _apply_layer_transformation(self, layer: str, data: Dict[str, Any], 
                                  spiral_position: float) -> Dict[str, Any]:
        """Apply transformation specific to each vortex layer."""
        if layer == "raw_perception":
            # Add spiral distortion to raw data
            return {
                **data,
                "spiral_enhancement": spiral_position,
                "perception_clarity": 1.0 + math.sin(spiral_position) * 0.1
            }
        
        elif layer == "pattern_recognition":
            # Identify recurring patterns in the data
            patterns = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    # Simple pattern: oscillation detection
                    patterns.append(f"pattern_{key}_{math.cos(spiral_position):.2f}")
            
            return {
                **data,
                "recognized_patterns": patterns,
                "pattern_confidence": abs(math.cos(spiral_position))
            }
        
        elif layer == "conceptual_abstraction":
            # Abstract concepts from patterns
            concepts = []
            if "recognized_patterns" in data:
                for pattern in data["recognized_patterns"]:
                    concepts.append(f"concept_from_{pattern}")
            
            return {
                **data,
                "abstract_concepts": concepts,
                "abstraction_level": spiral_position % 1.0
            }
        
        elif layer == "relational_inference":
            # Infer relationships between concepts
            relationships = []
            if "abstract_concepts" in data:
                concepts = data["abstract_concepts"]
                for i, concept1 in enumerate(concepts):
                    for concept2 in concepts[i+1:]:
                        relationships.append(f"relation_{concept1}_to_{concept2}")
            
            return {
                **data,
                "inferred_relationships": relationships,
                "relational_complexity": len(relationships)
            }
        
        elif layer == "meta_knowledge_synthesis":
            # Synthesize meta-knowledge from all layers
            meta_knowledge = {
                "synthesis_timestamp": time.time(),
                "spiral_completion": spiral_position,
                "knowledge_density": len(str(data)),
                "transformation_depth": len(self.transformation_layers),
                "vortex_cycle": self.metamorphosis_stage
            }
            
            return {
                **data,
                "meta_knowledge": meta_knowledge,
                "synthesis_complete": True
            }
        
        return data
    
    def get_vortex_state(self) -> Dict[str, Any]:
        """Get current state of the inference vortex."""
        return {
            "vortex_id": self.vortex_id,
            "intensity": self.intensity,
            "direction": self.rotation_direction,
            "metamorphosis_stage": self.metamorphosis_stage,
            "knowledge_spiral_depth": len(self.knowledge_spiral),
            "transformation_layers": len(self.transformation_layers)
        }


@dataclass
class AgenticEventLoop:
    """
    Dynamic agentic event loop that drives inference vortices into metamorphosis.
    
    Manages the temporal dynamics of agent cognition, orchestrating
    the transformation cycles that enable agent evolution.
    """
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    cycle_frequency: float = 1.0  # Hz
    metamorphosis_threshold: int = 5
    event_queue: List[Dict[str, Any]] = field(default_factory=list)
    vortices: List[InferenceVortex] = field(default_factory=list)
    metamorphosis_count: int = 0
    loop_state: str = "initializing"  # initializing, running, metamorphing, evolved
    
    def add_vortex(self, vortex: InferenceVortex):
        """Add an inference vortex to the event loop."""
        self.vortices.append(vortex)
    
    def queue_event(self, event_type: str, data: Dict[str, Any]):
        """Queue an event for processing in the next cycle."""
        event = {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
            "processed": False
        }
        self.event_queue.append(event)
    
    def process_cycle(self) -> Dict[str, Any]:
        """Process one complete agentic event loop cycle."""
        cycle_start = time.time()
        processed_events = []
        vortex_outputs = []
        
        # Set loop state
        if self.loop_state == "initializing":
            self.loop_state = "running"
        
        # Process queued events through vortices
        for event in self.event_queue:
            if not event["processed"]:
                # Route event through all vortices
                event_outputs = []
                for vortex in self.vortices:
                    output = vortex.process_through_vortex(event["data"])
                    event_outputs.append({
                        "vortex_id": vortex.vortex_id,
                        "output": output
                    })
                
                event["processed"] = True
                event["vortex_outputs"] = event_outputs
                processed_events.append(event)
                vortex_outputs.extend(event_outputs)
        
        # Clear processed events
        self.event_queue = [e for e in self.event_queue if not e["processed"]]
        
        # Check for metamorphosis conditions
        metamorphosis_triggered = self._check_metamorphosis_conditions()
        
        if metamorphosis_triggered:
            self.loop_state = "metamorphing"
            metamorphosis_result = self._trigger_metamorphosis()
        else:
            metamorphosis_result = None
        
        cycle_duration = time.time() - cycle_start
        
        return {
            "cycle_id": str(uuid.uuid4()),
            "processed_events": len(processed_events),
            "vortex_outputs": vortex_outputs,
            "metamorphosis_triggered": metamorphosis_triggered,
            "metamorphosis_result": metamorphosis_result,
            "cycle_duration": cycle_duration,
            "loop_state": self.loop_state,
            "cycle_frequency": self.cycle_frequency
        }
    
    def _check_metamorphosis_conditions(self) -> bool:
        """Check if conditions are met for triggering metamorphosis."""
        # Count vortices that have completed sufficient cycles
        mature_vortices = sum(1 for v in self.vortices 
                             if len(v.knowledge_spiral) >= self.metamorphosis_threshold)
        
        # Trigger metamorphosis if enough vortices are mature
        return mature_vortices >= len(self.vortices) * 0.6  # 60% threshold
    
    def _trigger_metamorphosis(self) -> Dict[str, Any]:
        """Trigger metamorphosis transformation of the agent."""
        self.metamorphosis_count += 1
        
        # Collect knowledge from all vortices
        collective_knowledge = []
        for vortex in self.vortices:
            if vortex.knowledge_spiral:
                collective_knowledge.extend(vortex.knowledge_spiral)
        
        # Reset vortices for new cycle
        for vortex in self.vortices:
            vortex.knowledge_spiral = []
            vortex.metamorphosis_stage = 0
            # Slightly increase intensity for evolution
            vortex.intensity = min(2.0, vortex.intensity * 1.1)
        
        # Mark as evolved
        self.loop_state = "evolved"
        
        return {
            "metamorphosis_id": str(uuid.uuid4()),
            "metamorphosis_count": self.metamorphosis_count,
            "knowledge_integrated": len(collective_knowledge),
            "vortices_evolved": len(self.vortices),
            "evolution_timestamp": time.time()
        }
    
    def get_loop_status(self) -> Dict[str, Any]:
        """Get current status of the agentic event loop."""
        return {
            "loop_id": self.loop_id,
            "state": self.loop_state,
            "metamorphosis_count": self.metamorphosis_count,
            "active_vortices": len(self.vortices),
            "queued_events": len(self.event_queue),
            "cycle_frequency": self.cycle_frequency
        }


@dataclass
class FeedbackLoop:
    """
    Virtual engine feedback loop for training and homeostasis achievement.
    
    Implements adaptive learning mechanisms that use feedback to achieve
    and maintain equilibrium states through continuous adjustment.
    """
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    loop_type: str = "homeostatic"  # homeostatic, learning, adaptive, equilibrium
    target_value: float = 1.0
    current_value: float = 0.5
    error_history: List[float] = field(default_factory=list)
    control_output_history: List[float] = field(default_factory=list)
    
    # PID controller parameters for sophisticated feedback control
    kp: float = 1.0  # Proportional gain
    ki: float = 0.1  # Integral gain  
    kd: float = 0.05  # Derivative gain
    
    integral_sum: float = 0.0
    previous_error: float = 0.0
    learning_rate: float = 0.01
    adaptation_factor: float = 0.05
    
    def update_feedback(self, current_measurement: float, dt: float = 1.0) -> float:
        """Update feedback loop with current measurement and return control output."""
        self.current_value = current_measurement
        error = self.target_value - self.current_value
        
        # Store error history
        self.error_history.append(error)
        if len(self.error_history) > 100:  # Keep limited history
            self.error_history = self.error_history[-50:]
        
        # PID control calculation
        proportional = self.kp * error
        
        # Integral term (accumulated error over time)
        self.integral_sum += error * dt
        integral = self.ki * self.integral_sum
        
        # Derivative term (rate of error change)
        derivative = self.kd * (error - self.previous_error) / dt if dt > 0 else 0
        self.previous_error = error
        
        # Combined control output
        control_output = proportional + integral + derivative
        
        # Apply adaptation based on loop type
        if self.loop_type == "learning":
            control_output = self._apply_learning_adaptation(control_output)
        elif self.loop_type == "adaptive":
            control_output = self._apply_adaptive_modification(control_output)
        elif self.loop_type == "equilibrium":
            control_output = self._apply_equilibrium_maintenance(control_output)
        
        # Store control output history
        self.control_output_history.append(control_output)
        if len(self.control_output_history) > 100:
            self.control_output_history = self.control_output_history[-50:]
        
        return control_output
    
    def _apply_learning_adaptation(self, control_output: float) -> float:
        """Apply learning-based adaptation to control output."""
        # Adjust gains based on error patterns
        if len(self.error_history) >= 5:
            recent_errors = self.error_history[-5:]
            error_variance = sum((e - sum(recent_errors)/len(recent_errors))**2 for e in recent_errors) / len(recent_errors)
            
            # If high variance, increase derivative gain to reduce oscillation
            if error_variance > 0.1:
                self.kd = min(0.2, self.kd + self.learning_rate)
            else:
                self.kd = max(0.01, self.kd - self.learning_rate * 0.5)
        
        return control_output
    
    def _apply_adaptive_modification(self, control_output: float) -> float:
        """Apply adaptive modification based on system behavior."""
        # Adapt proportional gain based on error magnitude
        if abs(self.previous_error) > 0.5:
            self.kp = min(2.0, self.kp + self.adaptation_factor)
        elif abs(self.previous_error) < 0.1:
            self.kp = max(0.5, self.kp - self.adaptation_factor * 0.5)
        
        return control_output
    
    def _apply_equilibrium_maintenance(self, control_output: float) -> float:
        """Apply equilibrium maintenance adjustments."""
        # If close to target, reduce control effort to prevent overshoot
        if abs(self.previous_error) < 0.05:
            control_output *= 0.8
        
        # Reset integral sum if crossing setpoint to prevent windup
        if len(self.error_history) >= 2:
            if (self.error_history[-1] * self.error_history[-2]) < 0:  # Sign change
                self.integral_sum *= 0.5
        
        return control_output
    
    def set_target(self, new_target: float):
        """Set new target value for the feedback loop."""
        self.target_value = new_target
        # Reset integral sum when target changes
        self.integral_sum = 0.0
    
    def get_loop_performance(self) -> Dict[str, Any]:
        """Get performance metrics of the feedback loop."""
        if not self.error_history:
            return {"status": "no_data"}
        
        recent_errors = self.error_history[-10:] if len(self.error_history) >= 10 else self.error_history
        
        return {
            "loop_id": self.loop_id,
            "loop_type": self.loop_type,
            "current_error": self.error_history[-1] if self.error_history else 0,
            "mean_error": sum(recent_errors) / len(recent_errors),
            "error_variance": sum((e - sum(recent_errors)/len(recent_errors))**2 for e in recent_errors) / len(recent_errors),
            "steady_state_achieved": abs(self.error_history[-1]) < 0.05 if self.error_history else False,
            "oscillation_detected": self._detect_oscillation(),
            "gains": {"kp": self.kp, "ki": self.ki, "kd": self.kd}
        }
    
    def _detect_oscillation(self) -> bool:
        """Detect if the system is oscillating."""
        if len(self.error_history) < 6:
            return False
        
        recent_errors = self.error_history[-6:]
        sign_changes = sum(1 for i in range(1, len(recent_errors)) 
                          if recent_errors[i] * recent_errors[i-1] < 0)
        
        return sign_changes >= 3  # Oscillating if 3+ sign changes in 6 samples


@dataclass
class VirtualEngine:
    """
    Virtual engine that orchestrates feedback loops for training and homeostasis.
    
    Manages multiple feedback loops to achieve complex system regulation
    and continuous improvement through adaptive learning.
    """
    engine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    feedback_loops: Dict[str, FeedbackLoop] = field(default_factory=dict)
    training_sessions: List[Dict[str, Any]] = field(default_factory=list)
    homeostatic_targets: Dict[str, float] = field(default_factory=dict)
    equilibrium_state: bool = False
    last_update: float = field(default_factory=time.time)
    
    def __post_init__(self):
        # Initialize default homeostatic targets
        if not self.homeostatic_targets:
            self.homeostatic_targets = {
                "coherence": 0.8,
                "stability": 0.9,
                "entropy": 0.3,  # Lower is better for entropy
                "learning_rate": 0.7
            }
        
        # Create feedback loops for each target
        for target_name, target_value in self.homeostatic_targets.items():
            loop_type = "equilibrium" if target_name in ["coherence", "stability"] else "homeostatic"
            self.feedback_loops[target_name] = FeedbackLoop(
                agent_id=self.agent_id,
                loop_type=loop_type,
                target_value=target_value
            )
    
    def update_measurements(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """Update all feedback loops with current measurements."""
        dt = time.time() - self.last_update
        self.last_update = time.time()
        
        control_outputs = {}
        
        for measurement_name, measurement_value in measurements.items():
            if measurement_name in self.feedback_loops:
                loop = self.feedback_loops[measurement_name]
                control_output = loop.update_feedback(measurement_value, dt)
                control_outputs[measurement_name] = control_output
        
        # Check for equilibrium achievement
        self.equilibrium_state = self._check_equilibrium_state()
        
        return control_outputs
    
    def _check_equilibrium_state(self) -> bool:
        """Check if all feedback loops have achieved equilibrium."""
        if not self.feedback_loops:
            return False
        
        equilibrium_count = 0
        for loop in self.feedback_loops.values():
            performance = loop.get_loop_performance()
            if performance.get("steady_state_achieved", False) and not performance.get("oscillation_detected", True):
                equilibrium_count += 1
        
        # Equilibrium achieved if 80% of loops are stable
        return equilibrium_count >= len(self.feedback_loops) * 0.8
    
    def start_training_session(self, session_type: str = "adaptive") -> str:
        """Start a new training session."""
        session_id = str(uuid.uuid4())
        
        session = {
            "session_id": session_id,
            "session_type": session_type,
            "start_time": time.time(),
            "initial_state": self._capture_current_state(),
            "adaptations_made": [],
            "performance_metrics": []
        }
        
        self.training_sessions.append(session)
        
        # Adjust feedback loops for training
        if session_type == "adaptive":
            for loop in self.feedback_loops.values():
                loop.learning_rate *= 1.5  # Increase learning rate for training
        
        return session_id
    
    def _capture_current_state(self) -> Dict[str, Any]:
        """Capture current state of all feedback loops."""
        state = {}
        for name, loop in self.feedback_loops.items():
            state[name] = {
                "current_value": loop.current_value,
                "target_value": loop.target_value,
                "gains": {"kp": loop.kp, "ki": loop.ki, "kd": loop.kd},
                "error": loop.previous_error
            }
        return state
    
    def end_training_session(self, session_id: str) -> Dict[str, Any]:
        """End a training session and return results."""
        session = None
        for s in self.training_sessions:
            if s["session_id"] == session_id:
                session = s
                break
        
        if not session:
            return {"error": "Session not found"}
        
        # Capture final state
        final_state = self._capture_current_state()
        session["end_time"] = time.time()
        session["final_state"] = final_state
        session["duration"] = session["end_time"] - session["start_time"]
        
        # Calculate improvements
        improvements = {}
        for name in self.feedback_loops.keys():
            initial_error = abs(session["initial_state"][name]["error"])
            final_error = abs(final_state[name]["error"])
            improvements[name] = (initial_error - final_error) / initial_error if initial_error > 0 else 0
        
        session["improvements"] = improvements
        
        # Reset learning rates
        for loop in self.feedback_loops.values():
            loop.learning_rate = 0.01
        
        return session
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get current status of the virtual engine."""
        loop_performances = {}
        for name, loop in self.feedback_loops.items():
            loop_performances[name] = loop.get_loop_performance()
        
        return {
            "engine_id": self.engine_id,
            "equilibrium_achieved": self.equilibrium_state,
            "active_feedback_loops": len(self.feedback_loops),
            "training_sessions_completed": len(self.training_sessions),
            "loop_performances": loop_performances,
            "homeostatic_targets": self.homeostatic_targets,
            "last_update": self.last_update
        }


@dataclass
class AutopoieticProcess:
    """
    Autopoietic process for self-maintenance and self-organization.
    
    Implements self-creating and self-maintaining systems that can
    project homeostatic images and enable feedforward prediction.
    """
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    process_type: str = "self_maintenance"  # self_maintenance, self_organization, self_reproduction
    components: Dict[str, Any] = field(default_factory=dict)
    organization_pattern: List[str] = field(default_factory=list)
    autopoietic_network: Dict[str, List[str]] = field(default_factory=dict)
    closure_achieved: bool = False
    self_reference_depth: int = 0
    emergence_stage: str = "initialization"  # initialization, organization, closure, autopoiesis
    
    def __post_init__(self):
        if not self.organization_pattern:
            self.organization_pattern = [
                "component_production",
                "network_formation", 
                "boundary_establishment",
                "self_reference_creation",
                "autopoietic_closure"
            ]
        
        # Initialize basic components for self-maintenance
        if not self.components:
            self.components = {
                "catalyst": {"activity": 0.5, "stability": 0.8},
                "substrate": {"availability": 1.0, "quality": 0.7},
                "product": {"concentration": 0.3, "viability": 0.6},
                "boundary": {"integrity": 0.9, "permeability": 0.4}
            }
    
    def execute_autopoietic_cycle(self) -> Dict[str, Any]:
        """Execute one complete autopoietic cycle."""
        cycle_results = {
            "cycle_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "initial_state": dict(self.components),
            "operations_performed": [],
            "emergence_transitions": []
        }
        
        # Execute each stage of organization pattern
        for stage in self.organization_pattern:
            operation_result = self._execute_stage(stage)
            cycle_results["operations_performed"].append(operation_result)
            
            # Check for emergence transitions
            if self._check_emergence_transition():
                transition = self._advance_emergence_stage()
                cycle_results["emergence_transitions"].append(transition)
        
        # Update autopoietic network
        self._update_autopoietic_network()
        
        # Check for autopoietic closure
        self.closure_achieved = self._check_autopoietic_closure()
        
        cycle_results.update({
            "final_state": dict(self.components),
            "closure_achieved": self.closure_achieved,
            "emergence_stage": self.emergence_stage,
            "self_reference_depth": self.self_reference_depth,
            "network_connectivity": len(self.autopoietic_network)
        })
        
        return cycle_results
    
    def _execute_stage(self, stage: str) -> Dict[str, Any]:
        """Execute a specific stage of the autopoietic process."""
        if stage == "component_production":
            return self._produce_components()
        elif stage == "network_formation":
            return self._form_network_connections()
        elif stage == "boundary_establishment":
            return self._establish_boundaries()
        elif stage == "self_reference_creation":
            return self._create_self_reference()
        elif stage == "autopoietic_closure":
            return self._achieve_closure()
        
        return {"stage": stage, "status": "unknown"}
    
    def _produce_components(self) -> Dict[str, Any]:
        """Produce new components through catalytic processes."""
        # Catalyst transforms substrate into product
        catalyst_activity = self.components["catalyst"]["activity"]
        substrate_availability = self.components["substrate"]["availability"]
        
        production_rate = catalyst_activity * substrate_availability * 0.1
        
        # Update component concentrations
        self.components["product"]["concentration"] += production_rate
        self.components["substrate"]["availability"] -= production_rate * 0.5
        
        # Catalyst may degrade slightly
        self.components["catalyst"]["stability"] -= 0.01
        
        # Regenerate catalyst if product concentration is sufficient
        if self.components["product"]["concentration"] > 0.5:
            self.components["catalyst"]["activity"] = min(1.0, 
                self.components["catalyst"]["activity"] + 0.05)
        
        return {
            "stage": "component_production",
            "production_rate": production_rate,
            "catalyst_activity": catalyst_activity,
            "new_product_level": self.components["product"]["concentration"]
        }
    
    def _form_network_connections(self) -> Dict[str, Any]:
        """Form network connections between components."""
        connections_formed = 0
        
        # Create connections based on component compatibility
        component_names = list(self.components.keys())
        for i, comp1 in enumerate(component_names):
            for comp2 in component_names[i+1:]:
                # Connection probability based on component activities/levels
                comp1_level = list(self.components[comp1].values())[0]
                comp2_level = list(self.components[comp2].values())[0]
                
                connection_prob = (comp1_level + comp2_level) / 2
                
                if random.random() < connection_prob * 0.3:  # 30% max connection rate
                    if comp1 not in self.autopoietic_network:
                        self.autopoietic_network[comp1] = []
                    if comp2 not in self.autopoietic_network[comp1]:
                        self.autopoietic_network[comp1].append(comp2)
                        connections_formed += 1
        
        return {
            "stage": "network_formation",
            "connections_formed": connections_formed,
            "total_connections": sum(len(connections) for connections in self.autopoietic_network.values()),
            "network_density": len(self.autopoietic_network) / len(self.components) if self.components else 0
        }
    
    def _establish_boundaries(self) -> Dict[str, Any]:
        """Establish system boundaries."""
        # Boundary integrity depends on component stability
        avg_stability = sum(
            comp.get("stability", comp.get("integrity", list(comp.values())[0])) 
            for comp in self.components.values()
        ) / len(self.components)
        
        self.components["boundary"]["integrity"] = avg_stability
        
        # Permeability adjusts based on system needs
        if self.components["substrate"]["availability"] < 0.3:
            # Increase permeability to allow more substrate in
            self.components["boundary"]["permeability"] = min(1.0,
                self.components["boundary"]["permeability"] + 0.1)
        elif self.components["product"]["concentration"] > 0.8:
            # Decrease permeability to retain products
            self.components["boundary"]["permeability"] = max(0.1,
                self.components["boundary"]["permeability"] - 0.1)
        
        return {
            "stage": "boundary_establishment",
            "boundary_integrity": self.components["boundary"]["integrity"],
            "boundary_permeability": self.components["boundary"]["permeability"],
            "boundary_effectiveness": avg_stability
        }
    
    def _create_self_reference(self) -> Dict[str, Any]:
        """Create self-referential structures."""
        # Self-reference emerges when the system can model itself
        self_modeling_capability = 0.0
        
        # Check if network can represent itself
        if len(self.autopoietic_network) >= 3:  # Minimum complexity for self-reference
            network_complexity = sum(len(connections) for connections in self.autopoietic_network.values())
            component_diversity = len(set(list(self.components.keys())))
            
            self_modeling_capability = min(1.0, (network_complexity * component_diversity) / 20.0)
        
        # Increase self-reference depth
        if self_modeling_capability > 0.5:
            self.self_reference_depth += 1
        
        return {
            "stage": "self_reference_creation",
            "self_modeling_capability": self_modeling_capability,
            "self_reference_depth": self.self_reference_depth,
            "reflexivity_achieved": self_modeling_capability > 0.7
        }
    
    def _achieve_closure(self) -> Dict[str, Any]:
        """Achieve autopoietic closure."""
        # Closure achieved when system produces its own components
        closure_indicators = []
        
        # Check if products can serve as catalysts (closure)
        if (self.components["product"]["concentration"] > 0.6 and 
            self.components["catalyst"]["activity"] > 0.5):
            closure_indicators.append("catalytic_closure")
        
        # Check if network is self-maintaining
        if (len(self.autopoietic_network) >= 2 and 
            self.components["boundary"]["integrity"] > 0.7):
            closure_indicators.append("structural_closure")
        
        # Check if self-reference enables self-production
        if self.self_reference_depth >= 2:
            closure_indicators.append("informational_closure")
        
        closure_level = len(closure_indicators) / 3.0  # Three types of closure
        
        return {
            "stage": "autopoietic_closure",
            "closure_indicators": closure_indicators,
            "closure_level": closure_level,
            "full_closure_achieved": closure_level >= 0.67
        }
    
    def _update_autopoietic_network(self):
        """Update the autopoietic network structure."""
        # Remove weak connections
        for component, connections in list(self.autopoietic_network.items()):
            if component in self.components:
                comp_strength = list(self.components[component].values())[0]
                # Remove connections if component is weak
                if comp_strength < 0.2:
                    filtered_connections = [c for c in connections 
                                          if c in self.components and 
                                          list(self.components[c].values())[0] > 0.3]
                    self.autopoietic_network[component] = filtered_connections
    
    def _check_emergence_transition(self) -> bool:
        """Check if conditions are met for emergence transition."""
        if self.emergence_stage == "initialization":
            return sum(list(comp.values())[0] for comp in self.components.values()) > 2.0
        elif self.emergence_stage == "organization":
            return len(self.autopoietic_network) >= 2
        elif self.emergence_stage == "closure":
            return self.self_reference_depth >= 1
        elif self.emergence_stage == "autopoiesis":
            return self.closure_achieved
        
        return False
    
    def _advance_emergence_stage(self) -> Dict[str, Any]:
        """Advance to the next emergence stage."""
        previous_stage = self.emergence_stage
        
        if self.emergence_stage == "initialization":
            self.emergence_stage = "organization"
        elif self.emergence_stage == "organization":
            self.emergence_stage = "closure"
        elif self.emergence_stage == "closure":
            self.emergence_stage = "autopoiesis"
        
        return {
            "transition": f"{previous_stage} -> {self.emergence_stage}",
            "timestamp": time.time()
        }
    
    def _check_autopoietic_closure(self) -> bool:
        """Check if full autopoietic closure is achieved."""
        # Full closure requires all components to be self-produced
        catalyst_self_produced = self.components["product"]["concentration"] > 0.5
        boundary_maintained = self.components["boundary"]["integrity"] > 0.6
        network_connected = len(self.autopoietic_network) >= 3
        self_referential = self.self_reference_depth >= 2
        
        return all([catalyst_self_produced, boundary_maintained, 
                   network_connected, self_referential])
    
    def get_autopoietic_status(self) -> Dict[str, Any]:
        """Get current status of the autopoietic process."""
        return {
            "process_id": self.process_id,
            "process_type": self.process_type,
            "emergence_stage": self.emergence_stage,
            "closure_achieved": self.closure_achieved,
            "self_reference_depth": self.self_reference_depth,
            "component_count": len(self.components),
            "network_connections": sum(len(connections) for connections in self.autopoietic_network.values()),
            "autopoietic_viability": self._calculate_viability()
        }
    
    def _calculate_viability(self) -> float:
        """Calculate overall autopoietic viability."""
        if not self.components:
            return 0.0
        
        # Average component strength
        component_strength = sum(list(comp.values())[0] for comp in self.components.values()) / len(self.components)
        
        # Network connectivity factor
        network_factor = min(1.0, len(self.autopoietic_network) / len(self.components))
        
        # Self-reference factor
        self_ref_factor = min(1.0, self.self_reference_depth / 3.0)
        
        # Closure factor
        closure_factor = 1.0 if self.closure_achieved else 0.5
        
        return (component_strength + network_factor + self_ref_factor + closure_factor) / 4.0


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