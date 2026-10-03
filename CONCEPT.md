# CommonGround — product concept

## Problem

Group recommendation often collapses two people into an average. That can hide a proposal that works extremely well for one person and poorly for the other.

CommonGround asks a narrower question:

> Can we find one movie that both people rank reasonably well, even when they arrive there from different cultural interests?

## Core interaction

Each person enters 1–3 films or artists they genuinely like.

Qloo resolves those interests, retrieves movie candidates for each profile and then evaluates the **same candidate union** for both people. CommonGround chooses the movie with the best worse-side rank.

The result card has two routes:

- Person A → Qloo-supported input connection → bridge movie
- Person B → Qloo-supported input connection → bridge movie

If explainability is unavailable for a result, the UI says so. It does not invent a psychological explanation.

## Agentic loop

The agent has a maximum of two rounds.

Round 1:
- resolve entities;
- discover candidates independently;
- union candidate IDs;
- evaluate identical pool for both people;
- propose one movie.

Feedback:
- both choose **Want to try** → success;
- either chooses **Already know** or **Not for me** → exclude that movie.

Round 2:
- widen retrieval from 20 to 40 candidates per side;
- keep the exclusion;
- re-evaluate the new shared pool;
- propose once more.

If both people still do not accept, CommonGround stops with no confirmed bridge.

## Why this is stronger than the old MVP

- no arbitrary `72/20/8` score;
- no percent-like satisfaction claims;
- no success threshold such as `0.75 = strong bridge`;
- no hash-based public recommendation engine;
- no intersection-only blind spot;
- no copied input labels pretending to be explainability;
- feedback changes the next query instead of merely decorating the UI.

## Scope

Target output is movie only. Inputs may be movies or artists. Restaurants are intentionally removed from this version.

No database, paid LLM, GPU, accounts or user profiling service is required.

