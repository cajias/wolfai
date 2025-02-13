.. image:: https://mermaid-js.github.io/mermaid/img/logo.svg
   :alt: Mermaid Logo
   :align: center

======================================================
Werewolf AI System - Strategic AI for Social Deduction
======================================================

This project aims to build an AI player for the **Werewolf** social deduction game. Werewolf is a game of deception and deduction in which players take on secret roles as either Villagers or Werewolves, with the goal of uncovering hidden identities through discussion, accusation, and voting. The AI should reason about the game, update its beliefs dynamically, and make optimal strategic decisions using **Prolog for logical inference, MiniZinc for constraint optimization, and probabilistic models (Bayesian Inference, HMMs, Kalman Filters, and POMDPs)**.

.. contents::
   :depth: 2
   :local:

Overview
========

The system consists of several key components working together to enable intelligent, strategic decision-making by the AI. Each component plays a distinct role in processing game information, maintaining structured reasoning, and optimizing gameplay strategies.

- **Arena (Game Master)**: Controls the game flow using a **state machine**.
- **AI Player**: An autonomous agent that plays the game, tracking its beliefs and adjusting strategies.
- **Multi-Agent System (MAS)**: Helps the AI reason about other players.
- **Prolog**: Handles logical deduction, checking for contradictions and logical inconsistencies.
- **MiniZinc**: Optimizes AI's strategic decisions based on available information.
- **Probability Models**: Bayesian Inference, HMMs, Kalman Filters, and POMDPs allow the AI to update and refine its beliefs.


System Architecture
===================

.. mermaid::

    graph TD;
        A[Arena (Game Master)] -->|Controls| B[State Machine];
        B -->|Manages| C[AI Player];
        B -->|Manages| D[Human Player];

        C -->|Maintains| E[Belief System];
        C -->|Uses| F[Memory System];
        C -->|Interacts With| A;

        E -->|Uses| G[Multi-Agent System];

        G -->|Queries| H[Prolog (Logic Engine)];
        G -->|Optimizes| I[MiniZinc (Strategy Optimizer)];
        G -->|Updates| J[Probability Models];

        F -->|Refines| E;

        J -->|Includes| K[Bayesian Inference];
        J -->|Includes| L[Hidden Markov Models (HMM)];
        J -->|Includes| M[Partially Observable MDP (POMDP)];
        J -->|Includes| N[Kalman Filters];

        D -->|Interacts With| A;


Game Flow
=========

The game follows a structured state machine managed by the **Arena**:

1. **Night Phase**: Werewolves secretly choose a target.
2. **Day Phase**: Players discuss and analyze game events.
3. **Accusation Phase**: Players can accuse others of being a Werewolf.
4. **Defense Phase**: The accused player defends themselves.
5. **Voting Phase**: Players vote on whether to eliminate the accused.
6. **Elimination Phase**: If the vote passes, the accused is removed, and their role is revealed.
7. **Game Continues** until a victory condition is met (Werewolves win or Villagers win).


AI Decision-Making
==================

The AI decision-making process is structured to simulate human-like deduction and strategic reasoning, ensuring that the agent adapts dynamically to new information while optimizing its actions within the game environment.

The AI operates as a **rational agent** in a **multi-agent system**, meaning it makes decisions based on a structured evaluation of available information, aiming to maximize its objectives while accounting for uncertainty and opponent behaviors., making decisions based on **belief updates, utility optimization, and reasoning under uncertainty**. Its decision-making process follows an **agent-based paradigm** with explicit knowledge representation and inference mechanisms:

1. **Belief Update (Perception Processing)**: The agent continuously integrates new observations (accusations, defenses, votes) into its internal **world model**, adjusting its probabilistic belief distribution over player roles.
2. **Logical Consistency Check (Prolog-Based Deduction)**: Using a **rule-based reasoning engine**, the agent ensures that its inferences do not contradict existing knowledge and prior deductions.
3. **Future State Simulation (Strategic Forecasting)**: The agent runs **counterfactual simulations** to model the potential consequences of different strategies, assessing the viability of accusations or defensive actions.
4. **Utility-Based Action Selection (MiniZinc Optimization)**: The agent employs **constraint satisfaction and utility-based decision-making** to determine the best action, balancing risk and reward within the current game phase.
5. **Action Execution (Behavior Enactment)**: The agent translates its optimized decision into a game action (accusation, defense, vote, or deception), influencing the game environment dynamically.

This structured decision-making pipeline enables the AI to behave as an **autonomous rational agent** with adaptive strategies and knowledge-driven reasoning.


Installation
============

To run this system, install the following dependencies:

 .. code-block:: bash

    source venv/bin/activate
    pip install -r requirements.txt



Running the Game
================

To start a simulation:

.. code-block:: bash

   python run_game.py

The AI will make decisions dynamically based on game state updates and probabilistic inference.


Contributors
============
- **Lead Architect:** Raul Cajias
- **AI Strategy & Design:** [Raul, Claude, ChatGPT]
- **Engineering Support:** Open for contributions!
