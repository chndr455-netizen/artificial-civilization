# Artificial Civilization

> **What happens if we stop designing the story, and start designing a world capable of creating its own stories?**

Artificial Civilization is an experimental project exploring the possibility of building a **persistent, evolving computational civilization** inhabited by autonomous artificial agents.

The idea is simple to describe, but probably a little crazy:

Instead of programming every event, every character, every political conflict, every invention, and every historical outcome, what if we build a world with enough underlying systems and relationships that **complex civilization can emerge from the interaction between them?**

The project is still very early.

Right now, the focus is the **World Engine**: a simulated natural environment containing terrain, weather, water, soil, vegetation, and other interconnected systems. Eventually, the goal is to introduce populations, agents, knowledge, economy, institutions, culture, technology, politics, and other systems that can interact with the natural world.

The long-term loop I have in mind looks something like:

```text
Natural World
      ↓
Agents experience the world
      ↓
Agents make decisions
      ↓
Actions change the world
      ↓
World systems produce consequences
      ↓
Agents learn from those consequences
      ↓
Knowledge accumulates
      ↓
Culture / technology / institutions emerge
      ↓
Civilization transforms the world
      ↓
The transformed world shapes civilization
      ↓
                    ...
```

The goal is **not to script a civilization**.

The goal is to create the conditions under which a civilization might develop.

---

## Why am I building this?

I've been fascinated by a question:

> **Can we build an artificial world where its inhabitants discover things that were never explicitly programmed as individual events?**

For example, rather than telling the simulation:

```text
"Deforestation causes political unrest."
```

we could model relationships such as:

```text
Trees ↓
→ runoff ↑
→ erosion ↑
→ soil quality ↓
→ agricultural productivity ↓
→ food supply ↓
→ food prices ↑
→ economic pressure ↑
→ social pressure ↑
→ political decisions
→ ...
```

The civilization would then experience the consequences through the systems of its world.

The creator defines the **possibility space**.

The inhabitants discover what is possible within it.

---

## This project is also an experiment in AI-assisted development

I am not a traditional software engineer.

A significant portion of this project is being developed through **AI-assisted coding / vibe coding**.

AI coding tools are helping write, explain, debug, and evolve the implementation while I focus heavily on:

* the overall vision
* system architecture
* conceptual models
* experiments
* questions about emergence
* deciding what the simulation should and should not control
* testing whether the resulting system behaves in interesting ways

This is intentional.

One of the experiments behind the project is therefore not only:

> "Can an artificial civilization emerge?"

but also:

> **"How far can a person with a crazy idea go by collaborating with AI coding systems?"**

The current code should therefore be considered **experimental and unfinished**. It may contain AI-generated code, questionable architectural decisions, bugs, simplifications, and things that will eventually need to be rewritten.

That's part of the experiment.

---

## Where this could eventually go

I honestly don't know.

That's one of the reasons this repository exists.

Maybe this becomes an interesting artificial-life experiment.

Maybe it becomes a research platform.

Maybe it becomes a simulation of artificial societies.

Maybe it becomes something completely different.

And one possibility that I find particularly exciting is **games**.

Imagine an MMORPG where the world isn't just a collection of scripted quests.

Instead:

* civilizations develop over time
* cities grow and decline
* economies respond to player actions
* resources are finite and spatially distributed
* politics emerge between factions
* wars have economic and environmental consequences
* NPC societies remember historical events
* technology develops through accumulated knowledge
* players become participants in a civilization rather than simply following a predetermined storyline
* the world continues evolving even when players are offline

In other words:

> **What if the game world itself was a simulation rather than just a stage for the game?**

I don't know whether this project will ever reach that level.

But I'd love to find out.

---

## Current Status

🚧 **Very early experimental development**

The current work focuses primarily on the **World Engine**.

The roadmap roughly looks like:

```text
v0.1  Minimal Natural World
      ↓
v0.2  Spatial World
      ↓
v0.3  Natural Ecosystem
      ↓
v0.4  Natural Resources
      ↓
v0.5  Human Impact
      ↓
v0.6  Basic Human Society
      ↓
v0.7  Economy
      ↓
v0.8  AI Agents
      ↓
v0.9  Memory / Knowledge / Institutions
      ↓
v1.0  Small Artificial Civilization
```

These versions are not promises or deadlines.

They are simply a way to keep the experiment moving incrementally.

---

## An Invitation

If you somehow stumbled across this repository and thought:

> **"Wait... I've been thinking about something like this too."**

Please reach out.

Seriously.

I'm especially interested in people who are fascinated by:

* artificial life
* agent-based simulation
* AI agents
* SLMs / LLMs
* emergent behavior
* artificial societies
* virtual worlds
* procedural worlds
* complex systems
* simulation
* game development
* MMORPG architecture
* economics
* artificial intelligence
* philosophy of emergence
* computational civilization

You don't need to agree with the architecture.

You don't even need to think the idea will work.

If you have a different perspective, a better approach, an interesting experiment, or simply think this is a wonderfully stupid idea worth trying 😂, I'd love to hear from you.

Maybe there are other crazy people out there thinking about the same problem.

Maybe we can build something together.

---

## Core Philosophy

A few principles currently guide the project:

> **Don't program the story. Build a world capable of creating stories.**

> **Don't program the consequences. Program the relationships that generate the consequences.**

> **The simulation should not decide what humans do. It should simulate the consequences of what they do.**

> **The creator defines the possibility space. The inhabitants discover what is possible within it.**

And perhaps the most important one:

> **There is no perfect civilization.**

A perfectly intelligent civilization would have very little left to discover.

The interesting civilization is one that is incomplete, makes mistakes, learns, forgets, adapts, conflicts, cooperates, creates, destroys, and changes the world that eventually changes it.

---

## If you're interested

Feel free to:

* explore the code
* open an issue
* propose an experiment
* suggest an architecture
* challenge an assumption
* fork the project
* tell me why this won't work
* or tell me how you think it could work better

This is an experiment.

Let's see how far it can go.

**License**: No open-source license has been selected yet. This project is currently shared publicly as an experimental work-in-progress. Licensing may change as the project evolves.
