#!/usr/bin/env python3
"""
Brains Behind the Bots — Classical Planning Playground (May 2025)

Run `python playground.py --help` for options.
Before first run:
    pip install "unified-planning[engines,plot]" networkx matplotlib tqdm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import networkx as nx
from tqdm.auto import tqdm

# ───────────────────────── Unified-Planning imports ───────────────────────── #
import unified_planning as up
from unified_planning.io import PDDLReader
from unified_planning.shortcuts import OneshotPlanner, SequentialSimulator
from unified_planning.engines import (
    PlanGenerationResultStatus as Status,
    Compiler,
    CompilationKind,
)

# Silence banner credits (UP 1.2 + API)
up.shortcuts.get_environment().credits_stream = None


# ────────────────────────────── PDDL builder ──────────────────────────────── #
class HanoiBuilder:
    """Generate Towers of Hanoi domain + problem PDDL files."""

    DOMAIN_PATH = Path("hanoi-domain.pddl")

    @staticmethod
    def domain() -> str:
        return """\
(define (domain hanoi)
  (:requirements :strips :typing :adl)
  (:types disk peg)
  (:predicates
      (clear ?x - object)
      (on ?d - disk ?p - peg)
      (smaller ?d1 - disk ?d2 - disk))
  (:action move
    :parameters (?d - disk ?from - peg ?to - peg)
    :precondition (and
        (on ?d ?from) (clear ?d) (clear ?to)
        (forall (?o - disk) (imply (on ?o ?from) (smaller ?d ?o))))
    :effect (and
        (on ?d ?to)
        (clear ?from)
        (not (on ?d ?from))
        (not (clear ?to))))
)"""

    @staticmethod
    def problem(n: int) -> str:
        discs = " ".join(f"d{i}" for i in range(1, n + 1))
        pegs = "p1 p2 p3"
        init = []

        # ordering relations
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                init.append(f"(smaller d{i} d{j})")

        init += [f"(on d{i} p1)" for i in range(1, n + 1)]
        init.append("(clear d1)")
        init += ["(clear p2)", "(clear p3)"]

        goal = " ".join(f"(on d{i} p3)" for i in range(1, n + 1))
        return f"""\
(define (problem hanoi-{n})
  (:domain hanoi)
  (:objects {discs} - disk {pegs} - peg)
  (:init {' '.join(init)})
  (:goal (and {goal}))
)""".replace("  ", " ")

    @classmethod
    def write_files(cls, sizes=(3, 5)) -> None:
        cls.DOMAIN_PATH.write_text(cls.domain())
        for n in sizes:
            Path(f"hanoi-{n}.pddl").write_text(cls.problem(n))


# ───────────────────────────── Planning helper ────────────────────────────── #
class Planner:
    """Facade for solving PDDL problems with UP engines."""

    def __init__(self, heuristic: str = "hff"):
        self.heuristic = heuristic

    def _read(self, domain: str | Path, problem: str | Path):
        reader = PDDLReader()
        return reader.parse_problem(str(domain), str(problem))

    def fast_downward(
            self, domain: str | Path, problem: str | Path
    ) -> Tuple[up.model.Problem, up.engines.results.PlanGenerationResult]:
        prob = self._read(domain, problem)
        with OneshotPlanner(
                name="fast-downward", params={"heuristic": self.heuristic}
        ) as p:
            res = p.solve(prob)
        return prob, res

    def pyperplan_compiled(
            self, domain: str | Path, problem: str | Path
    ) -> Tuple[up.model.Problem, up.engines.results.PlanGenerationResult]:
        orig = self._read(domain, problem)
        with Compiler(
                orig.kind, CompilationKind.QUANTIFIERS_REMOVING
        ) as comp:  # removes Forall
            comp_res = comp.compile(orig)
            stripped = comp_res.problem
        with OneshotPlanner(
                name="pyperplan", params={"heuristic": self.heuristic}
        ) as p:
            plan_res = p.solve(stripped)
        # translate plan back
        plan_res.plan = comp_res.convert_plan(plan_res.plan)
        return orig, plan_res


# ──────────────────────── State-space visualiser ─────────────────────────── #
class StateGraph:
    """Draw a partial search graph for small problems."""

    def __init__(self, problem: up.model.Problem, depth: int = 2):
        self.problem = problem
        self.depth = depth

    def build(self) -> nx.DiGraph:
        G = nx.DiGraph()
        with SequentialSimulator(self.problem) as sim:
            frontier = [(sim.get_initial_state(), 0)]
            seen = {frontier[0][0]}
            while frontier:
                state, d = frontier.pop()
                sid = id(state)
                G.add_node(sid)
                if d >= self.depth:
                    continue
                for act in self.problem.actions:
                    if sim.is_applicable(state, act):
                        nxt = sim.apply(state, act)
                        nid = id(nxt)
                        G.add_edge(sid, nid)
                        if nxt not in seen:
                            seen.add(nxt)
                            frontier.append((nxt, d + 1))
        return G

    def show(self) -> None:
        G = self.build()
        plt.figure(figsize=(8, 5))
        nx.draw_kamada_kawai(G, node_size=220, arrows=True, with_labels=False)
        plt.title(f"Partial state graph (depth ≤ {self.depth})")
        plt.show()


# ─────────────────────── FMAP multi-agent demo ───────────────────────────── #
class MultiAgentDemo:
    """Set up a two-robot swap problem and solve it with FMAP."""

    def run(self) -> None:
        from unified_planning.shortcuts import (
            Agent,
            MultiAgentProblem,
            Fluent,
            Object,
            user_type,
        )

        Location = user_type("Location")
        Robot = user_type("Robot")
        at = Fluent("at", Robot, Location)

        loc_a, loc_b = [Object(n, Location) for n in ("A", "B")]
        r1, r2 = [Object(n, Robot) for n in ("R1", "R2")]

        def add_move(agent: Agent):
            src = agent.parameter("src", Location)
            dst = agent.parameter("dst", Location)
            m = agent.action("move", src, dst)
            m.add_precondition(at(agent, src))
            m.add_effect(at(agent, src), False)
            m.add_effect(at(agent, dst), True)

        agents = []
        for rob in (r1, r2):
            ag = Agent(rob.name)
            ag.add_fluent(at)
            add_move(ag)
            agents.append(ag)

        prob = MultiAgentProblem("swap")
        for ag in agents:
            prob.add_agent(ag)
        prob.add_fluent(at)

        prob.set_initial_value(at(r1, loc_a), True)
        prob.set_initial_value(at(r2, loc_b), True)
        prob.add_goal(at(r1, loc_b))
        prob.add_goal(at(r2, loc_a))

        with OneshotPlanner(name="fmap", params={"heuristic": "hff"}) as p:
            res = p.solve(prob)

        print("FMAP status:", res.status)
        if res.plan:
            print("Multi-agent plan:")
            for a in res.plan.actions:
                print(" ", a)


# ──────────────────────────────── CLI ────────────────────────────────────── #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classical planning playground (UP 2025)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--discs", type=int, default=3, help="number of discs for Hanoi demo"
    )
    parser.add_argument(
        "--vis-depth", type=int, default=2, help="depth for state graph visual"
    )
    parser.add_argument(
        "--skip-vis", action="store_true", help="skip drawing the state graph"
    )
    parser.add_argument(
        "--skip-fmap", action="store_true", help="skip FMAP multi-agent demo"
    )
    args = parser.parse_args()

    # 1. build PDDL
    HanoiBuilder.write_files(sizes=(args.discs,))

    planner = Planner()

    # 2. solve with Fast Downward
    prob, res = planner.fast_downward(
        HanoiBuilder.DOMAIN_PATH, f"hanoi-{args.discs}.pddl"
    )
    if res.status != Status.SOLVED_SATISFICING:
        sys.exit(f"Fast Downward failed: {res.status}")
    print(f"Fast Downward plan ({len(res.plan.actions)} steps):")
    for a in res.plan.actions:
        print(" ", a)

    # 3. optional Pyperplan run
    _, res_pp = planner.pyperplan_compiled(
        HanoiBuilder.DOMAIN_PATH, f"hanoi-{args.discs}.pddl"
    )
    print(
        f"\nPyperplan (compiled) status: {res_pp.status} | "
        f"length: {len(res_pp.plan.actions)}"
    )

    # 4. graph visual
    if not args.skip_vis:
        sg = StateGraph(prob, depth=args.vis_depth)
        sg.show()

    # 5. FMAP demo
    if not args.skip_fmap:
        MultiAgentDemo().run()


if __name__ == "__main__":
    main()
