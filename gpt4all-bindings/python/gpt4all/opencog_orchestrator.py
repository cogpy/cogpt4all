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
                "event_loop_state": self.agentic_event_loop.get_loop_status()
            }
        
        return result


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