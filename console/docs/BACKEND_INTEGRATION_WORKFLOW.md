# 🎯 Backend Integration: Orchestration Workflow

**Status:** Ready to execute  
**Framework:** F-CONSOLE-0.1  
**Console Version:** 0.1.0 (PRODUCTION-READY)  
**Backend Phase:** CONTRACT ALIGNMENT  

---

## 📋 WORKFLOW OVERVIEW

```
┌─ PHASE 1: PROMPT & INTAKE (NOW) ─────────────┐
│                                              │
│  1. Send orchestration prompt to Claude      │
│     Sonnet (Backend Dev Senior)              │
│  2. Expect response with 3 sections:         │
│     • Backend inventory (factual)            │
│     • Endpoint gap matrix                    │
│     • Critical gaps list                     │
│  3. Receive response                         │
│                                              │
└──────────────────────────────────────────────┘
              ↓
┌─ PHASE 2: EVALUATION (IMMEDIATE) ───────────┐
│                                              │
│  1. Use EVALUATION_TEMPLATE.md to grade      │
│  2. Compare against IDEAL_RESPONSE_REFERENCE │
│  3. Identify gaps, blockers, surprises       │
│  4. Make GO/NO-GO decision                   │
│                                              │
└──────────────────────────────────────────────┘
              ↓
┌─ PHASE 3: SPEC GENERATION (IF GO) ──────────┐
│                                              │
│  1. Create docs/INTEGRATION_SPEC.md          │
│     ├─ Detailed adapter endpoints            │
│     ├─ Code examples (response format)       │
│     └─ Testing scenarios                     │
│  2. Create docs/BACKEND_CONTRACT_GAPS.md     │
│     ├─ Gap list (prioritized)                │
│     ├─ Fix procedures (step-by-step)         │
│     └─ Acceptance criteria                   │
│                                              │
└──────────────────────────────────────────────┘
              ↓
┌─ PHASE 4: IMPLEMENTATION (BACKEND TEAM) ───┐
│                                             │
│  Backend Dev Senior implements per:         │
│  ✓ Orchestration prompt                     │
│  ✓ Integration spec                         │
│  ✓ Gap fixes list                           │
│                                             │
│  Deliverables:                              │
│  ✓ 4 public endpoints (/api/execute, etc.)  │
│  ✓ Integration tests                        │
│  ✓ Updated docs                             │
│                                             │
└──────────────────────────────────────────────┘
              ↓
┌─ PHASE 5: VALIDATION & DEPLOYMENT ─────────┐
│                                             │
│  Console Dev Lead validates:                │
│  1. Test endpoints against contract         │
│  2. Run integration test suite               │
│  3. Verify error scenarios                  │
│  4. docker-compose full stack test          │
│                                             │
│  If PASS → Go to deployment                 │
│  If FAIL → Loop back to implementation      │
│                                             │
└──────────────────────────────────────────────┘
              ↓
┌─ PHASE 6: PRODUCTION DEPLOYMENT ───────────┐
│                                             │
│  1. Both images built & tagged              │
│  2. docker-compose up tested locally        │
│  3. docker network verified (techno-net)    │
│  4. API endpoints verified                  │
│  5. Audit trail verified                    │
│  6. Deploy to production                    │
│                                             │
└──────────────────────────────────────────────┘
```

---

## 📚 DOCUMENTS TO USE (IN ORDER)

### PHASE 1: Prompt & Intake

**File:** `docs/BACKEND_ORCHESTRATION_PROMPT.md`

**What:** Official orchestration prompt for Claude Sonnet  
**Why:** Structured intake, prevents scope creep, clear requirements  
**Action:** Copy & paste into your Backend Dev conversation  

**Key sections:**
- ⚠️ IMPORTANT CONTEXT (contract alignment, not greenfield)
- 📋 SECTION 1: Backend inventory template
- 📋 SECTION 2: Endpoint gap matrix template
- 📋 SECTION 3: Critical gaps list template

---

### PHASE 2: Evaluation

**File:** `docs/BACKEND_RESPONSE_EVALUATION_TEMPLATE.md`

**What:** Objective grading rubric for backend response  
**Why:** Fair, criterion-based evaluation (not subjective)  
**Action:** Fill out after receiving backend response

**Sections:**
- ✅ Section 1 assessment (each layer)
- ✅ Section 2 assessment (each endpoint)
- ✅ Section 3 assessment (gaps prioritized)
- 📊 Overall readiness score

**Output:** GO/NO-GO decision + timeline estimate

---

### PHASE 3: Reference Comparison

**File:** `docs/BACKEND_IDEAL_RESPONSE_REFERENCE.md`

**What:** "Gold standard" response for comparison  
**Why:** Know what GOOD looks like before you see REAL  
**Action:** Read BEFORE receiving actual response, then compare

**Includes:**
- 🎯 Ideal Section 1 (inventory with specifics)
- 🎯 Ideal Section 2 (gap matrix, low effort)
- 🎯 Ideal Section 3 (0 critical gaps, 2-3 week timeline)
- 🚨 Red flags (what would indicate problems)

---

## 🎯 STEP-BY-STEP EXECUTION GUIDE

### STEP 1: Prepare & Send Prompt (5 min)

```bash
1. Open docs/BACKEND_ORCHESTRATION_PROMPT.md
2. Copy entire prompt
3. Start conversation with Claude Sonnet
4. Paste prompt
5. Add context: "Backend repo at d:\Projects\techno-os-backend"
6. Send message
```

**Expected response time:** 30-60 minutes for detailed analysis

---

### STEP 2: Receive & Document Response (10 min)

```bash
1. Receive response from Claude Sonnet
2. Copy response into new file:
   docs/BACKEND_ACTUAL_RESPONSE_[DATE].md
3. Save for comparison
4. Read entire response carefully
5. Highlight any surprises or concerns
```

---

### STEP 3: Evaluate Using Template (15 min)

```bash
1. Open docs/BACKEND_RESPONSE_EVALUATION_TEMPLATE.md
2. Read Sections 1, 2, 3 of ACTUAL response
3. Check each checkbox in evaluation template
4. Fill in [describe if not passing] sections
5. Complete "Overall Assessment" section
6. Save filled template as:
   docs/BACKEND_EVALUATION_RESULTS_[DATE].md
```

---

### STEP 4: Compare Against Ideal (10 min)

```bash
1. Open docs/BACKEND_IDEAL_RESPONSE_REFERENCE.md
2. Compare ACTUAL vs. IDEAL for each section
3. Document deviations:
   - Expected differences (ok to differ)
   - Red flags (escalate immediately)
   - Gaps vs. risks (medium concern)
4. Note any red flags in evaluation results
```

---

### STEP 5: Make GO/NO-GO Decision (5 min)

Based on evaluation + comparison, decide:

**🟢 GO** (Proceed to Phase 3)
- ✅ All 3 sections complete & detailed
- ✅ Critical gaps: 0 or very minor
- ✅ Timeline: ≤3 weeks for integration
- ✅ No redesign of existing governance layers
- ✅ No red flags

**🟡 PROCEED WITH CAUTION** (Need clarification)
- ⚠️ Some details missing/unclear
- ⚠️ Minor gaps (1-2) with clear fixes
- ⚠️ Timeline: 2-4 weeks (acceptable)
- ⚠️ Suggests minor adjustments (not redesign)
- ⚠️ No red flags

**🔴 HOLD** (Need escalation)
- ❌ Critical gaps identified (3+)
- ❌ Red flags present
- ❌ Suggests redesign of existing layers
- ❌ Timeline: 4+ weeks (unacceptable)
- ❌ Incomplete response (not detailed)

---

### STEP 6: IF GO → Create Integration Spec (1-2 hours)

```bash
1. Using backend response + evaluation results
2. Create docs/INTEGRATION_SPEC.md:
   ├─ Adapter endpoints (detailed)
   ├─ Response schemas (with examples)
   ├─ Testing scenarios (happy path + errors)
   ├─ Docker composition (both services)
   └─ Deployment checklist

3. Create docs/BACKEND_CONTRACT_GAPS.md:
   ├─ Prioritized gap list
   ├─ Fix procedures (step-by-step)
   ├─ Code examples
   └─ Acceptance criteria

4. Send both specs to Backend Dev Senior
5. Clarify any open questions
```

---

### STEP 7: Backend Team Implements (Timeline per response)

Backend Dev Senior:
- ✓ Implements 4 public endpoints
- ✓ Follows integration specs exactly
- ✓ Writes integration tests
- ✓ Updates documentation
- ✓ Delivers code in docker-compose format

---

### STEP 8: Integration Testing (1-2 days)

Console Dev Lead:
```bash
1. Pull backend code
2. Update docker-compose to include both services
3. docker-compose up --build
4. Run integration tests:
   ├─ POST /api/execute (success path)
   ├─ GET /api/audit (success path)
   ├─ GET /api/memory (success path)
   ├─ Error scenarios (4XX, 5XX, timeout)
   ├─ Fail-closed behavior (unknown status)
   └─ Audit trail logging
5. If all PASS → deployment ready
6. If FAIL → loop back to backend team
```

---

## 📊 DECISION MATRIX

| Evaluation Result | Action | Timeline |
|------------------|--------|----------|
| 🟢 GO | Create specs, backend implements | 2-3 weeks |
| 🟡 CAUTION | Request clarification, minor specs | 3-4 weeks |
| 🔴 HOLD | Escalate, discuss trade-offs | 4+ weeks |

---

## 🎯 SUCCESS CRITERIA (End of Phase 3)

When specs are created, backend work is:

✅ Clearly defined (no ambiguity)  
✅ Scoped (4 endpoints, adapter pattern)  
✅ Testable (test scenarios in spec)  
✅ Documented (examples + expected responses)  
✅ Aligned with F-CONSOLE-0.1 (no governance changes)  
✅ Timeline-bounded (2-3 weeks max)  

---

## 📁 FILES CREATED FOR THIS WORKFLOW

```
d:\Projects\techno-os-console\docs\
├─ BACKEND_ORCHESTRATION_PROMPT.md
│  └─ The prompt to send to Claude Sonnet
│
├─ BACKEND_RESPONSE_EVALUATION_TEMPLATE.md
│  └─ Grading rubric (fill after response)
│
├─ BACKEND_IDEAL_RESPONSE_REFERENCE.md
│  └─ Gold standard (read before response)
│
├─ BACKEND_INTEGRATION_WORKFLOW.md (this file)
│  └─ Step-by-step execution guide
│
├─ [Generated during workflow]
├─ BACKEND_ACTUAL_RESPONSE_[DATE].md
├─ BACKEND_EVALUATION_RESULTS_[DATE].md
├─ INTEGRATION_SPEC.md (Phase 3)
└─ BACKEND_CONTRACT_GAPS.md (Phase 3)
```

---

## 🎓 KEY PRINCIPLES FOR THIS WORKFLOW

1. **Structured intake:** Prompt prevents scope creep
2. **Objective evaluation:** Template prevents bias
3. **Reference baseline:** Ideal response sets expectations
4. **Clear decision gate:** GO/NO-GO decision is explicit
5. **Documented specs:** Backend has zero ambiguity
6. **Testable output:** Integration tests verify alignment

---

## 🚀 READY TO EXECUTE?

### Checklist before sending prompt:

- [ ] Have you read BACKEND_ORCHESTRATION_PROMPT.md?
- [ ] Have you read BACKEND_IDEAL_RESPONSE_REFERENCE.md?
- [ ] Do you have backend workspace ready (d:\Projects\techno-os-backend)?
- [ ] Do you understand the 3-section response format?
- [ ] Do you have evaluation template prepared?

### If all checked → Ready to proceed!

```
Next action: Send BACKEND_ORCHESTRATION_PROMPT.md to Claude Sonnet
Expected: Detailed response with inventory + gaps + timeline
Evaluation: Use RESPONSE_EVALUATION_TEMPLATE.md
Decision: GO/HOLD based on evaluation results
```

---

**Framework:** F-CONSOLE-0.1 (Governance + Quality Gates)  
**Status:** Ready for backend integration phase  
**Risk Level:** Low (contract-driven, not greenfield)  
**Escalation:** If red flags → escalate to human decision-makers

> **"IA como instrumento. Humano como centro."**
>
> This workflow ensures AI agents (Console Dev + Backend Dev) stay aligned
> through explicit contracts, objective evaluation, and human oversight.
