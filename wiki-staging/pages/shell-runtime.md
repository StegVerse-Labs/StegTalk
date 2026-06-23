# Shell Runtime

## Purpose

The shell runtime describes StegTalk local shell state and shell actions. It connects contacts, inbox items, discovery results, and user view state into one local prototype runtime surface.

## Runtime Behavior

The shell path should identify:

- user entity
- active view
- contacts
- inbox items
- discovery results
- shell action
- updated shell state
- shell summary

## StegTalk Ownership

StegTalk owns the shell state shape, shell action runtime, local action dispatch, and shell demo trace.

## Overlap

StegGuardian may evaluate whether shell actions interact with account, recovery, or guardian boundaries. Admissibility may evaluate whether shell actions should be allowed, denied, or failed closed.

## Boundary

Shell readiness does not imply native iOS release, Android release, production push notifications, or external account sync.
