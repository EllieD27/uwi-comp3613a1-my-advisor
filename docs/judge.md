# student-judge competency report

**Judged at:** 2026-10-12T13:36:00-04:00
**Evidence pass:** fresh re-read of accessible native Copilot chats, current `docs/report.md`, all available phase evidence records, diagrams, wireframes, and deployment evidence; prior `docs/judge.md` ignored

**Student / session:** Eliana Dookhoo / MyAdvisor / COMP 3613A1
**Artifact:** Accessible Copilot Guide chats, six Guide-written/evidence transcript files, current report, UML/ERD artefacts, wireframes, and deployed app evidence
**Phases in evidence:** 1–6 (COMP 3613; Phase 5 polish, Phase 6 deploy)

## Totals

| | Count / value |
|--|--|
| Metrics on rubric | 12 (M1–M12) |
| N/A (excluded) | 0 |
| Metrics scored | 12 |
| Scoreable max | 48 |
| Awarded total | **44 / 48** |
| **Overall (avg of scored)** | **3.7 / 4** |
| Impression mark | **18 / 20** |

## Scorecard

| ID | Metric | Score / 4 | In avg | Evidence |
|----|--------|----------:|:------:|----------|
| M1 | Phase discipline | 4 | yes | The report contains the design artefacts before the implementation notes, Phase 5 includes multiple refinement passes, and Phase 6 deployment followed the local-workflow claim. |
| M2 | Problem framing | 4 | yes | The student-owned project, three `Feature (user)` workflows, use-case relationships, model rules, four wireframes, and branding decisions are all represented in the current report and phase evidence records. |
| M3 | Decision ownership | 4 | yes | The student made concrete domain decisions throughout Phase 5: Kate/Ian/Bob eligibility behavior, course classification, inclusion of advanced courses, and cross-application elective counts. |
| M4 | Artefact-before-code | 4 | yes | The UML PNG/JSON, Mermaid ERD, four wireframes, and implementation notes show that the build followed the assignment artefacts rather than replacing them with an unrelated design. |
| M5 | Verification habit | 3 | yes | The student stated that workflows worked locally, then continued reporting concrete mismatches and requested fixes. Deployment health, landing, and login behavior were also verified. A 4 is not awarded because the report does not preserve a detailed observation note for every screen. |
| M6 | Assignment fit | 4 | yes | The report documents FastStarter auth reuse, the layered routes/dependencies/schemas/services/repositories/models architecture, ERD-aligned workflows, theming, polish, and Render deployment. No inline-SQL route violation is evidenced. |
| M7 | Slice explanation | 3 | yes | The student explained domain behavior in their own words, for example “completed courses are shown in the eligible list” and “INFO 2605 is an elective,” then requested targeted cross-application corrections. The accessible record does not expose the earlier code-snippet exchanges, but the Guide did not establish a student refusal. |
| M8 | Prompt quality | 4 | yes | Prompts were concrete and testable: remove completed courses, add missing course codes, use a scrollbar, change “Year 2” to “Core,” and apply elective classification consistently. |
| M9 | Response to pushback | 4 | yes | The Phase 5 continuation shows sustained polish instead of accepting the first build: recommendation filtering, seeded student scenarios, labels, capacity/catalog behavior, and classification were revised across the application. |
| M10 | Integrity | 3 | yes | No paste-back, external-assist, suspicion, or edited-skill evidence was found; skill integrity is explicitly `pass`. The score reflects clean available evidence while acknowledging that earlier native chats are not accessible. |
| M11 | Provenance continuity | 3 | yes | The implementation and polish decisions remain consistent with MyAdvisor, the named workflows, model rules, wireframes, and seeded data. The unavailable native Phase 1–4 chats prevent a fully direct continuity trace, but the artefacts align. |
| M12 | Sincerity trajectory | 4 | yes | No suspicion round was entered, no sincerity blocks were required, and the accessible Phase 5 and Phase 6 turns show consistent student-owned correction requests through deployment. |

## Strengths

- All six COMP 3613 phases are represented: project/workflows, use cases, model, wireframes, theme/build/polish, and deployment.
- The student repeatedly found and corrected real workflow mismatches instead of stopping at the first successful build.
- The implementation stayed anchored to the MyAdvisor domain, wireframes, seeded users, course rules, and layered architecture.
- Deployment is complete and evidenced by the public URL and successful `/health` response.
- The report includes the required marker logins, diagrams, wireframes, implementation notes, transcripts package, and skill-integrity verification.

## Gaps (priority order)

1. The native Phase 1–4 chats are not available in the accessible project-session index. The report therefore uses clearly labeled artifact-based evidence records rather than fabricated dialogue.
2. The report could be stronger with brief student-observed screenshots or notes for each deployed workflow, but this is a documentation-strengthening opportunity, not a failed phase gate.

## Phase gate status

| Phase | Status | Note |
|-------|--------|------|
| 1 | met | MyAdvisor and three named workflows are recorded. |
| 2 | met | Use-case relationships, actor associations, and the UML PNG/JSON are present. |
| 3 | met | ERD entities, relationships, lifecycle rules, constraints, prerequisites, and grade rules are documented. |
| 4 | met | Four student-crafted wireframes are present and embedded in the report. |
| 5 | met | Theme, implementation, mismatch-driven refinement, model/data corrections, and local workflow completion are documented. |
| 6 | met | Public Render URL and marker logins are recorded; `/health` responds successfully. |

## Recommended next practice

- Add a short deployed verification note for each of the four main screens, recording the observed result and any final mismatch. This would make the already-complete Phase 5 evidence easier for a marker to audit.

## Integrity note

- **Clean on available evidence.** No external-assist/paste-back flag, suspicion spiral, or edited-skills finding was identified. Earlier native Phase 1–4 chats were unavailable, so their contents were not invented.

## Provenance flags

- Earlier native Phase 1–4 Guide chats unavailable to the report-building session.
- No edited-skills flag: `skill-integrity` is `pass`.
- No external-assist or transcript-gaming flag found.

## Sincerity log summary

- Blocks found: 0 | max round: 0 | min/mean/final confidence: not logged | trend: not applicable | cleared: yes

## Skips

- Skips: 0/3 used. No skip was recorded in the accessible Guide chats or current evidence records.
