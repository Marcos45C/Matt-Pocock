# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual strings used in this repo's issue tracker.

This repo uses the local-markdown tracker, so the strings go in each issue file's `Status:` line rather than in a label field.

| Label in mattpocock/skills | Value in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding string from this table.

Edit the "Value in our tracker" column to match whatever vocabulary you actually use.

## Implementation lifecycle

Implementation tickets add one terminal state to the triage roles:

| Value in our tracker | Meaning                                          |
| -------------------- | ------------------------------------------------ |
| `done`               | Implemented and verified; checklist complete     |

When an implementation ticket is finished: check its boxes, set `Status: done`, and leave a `## Comments` note with the commit and test result. A `Blocked by:` reference is satisfied when every ticket it lists is `done`.
