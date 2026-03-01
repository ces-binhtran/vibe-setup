# Local Skills File-Based Loading Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix local skill loading by updating CLAUDE.md and skill files to use file-based loading (Read tool) instead of broken Skill tool references.

**Architecture:** CLAUDE.md maps workflow checkpoints to skill file paths. Claude reads skill files directly using Read tool and follows their content.

**Tech Stack:** Markdown files, Claude Code Read tool

---

## Task 1: Update CLAUDE.md - Replace Skill-Driven Workflows Section

**Files:**
- Modify: `CLAUDE.md:11-21`

**Step 1: Read current CLAUDE.md section**

Run: Read tool on `CLAUDE.md:11-21`
Expected: See "Skill-Driven Workflows" section with `/vibe-rag:*` references

**Step 2: Replace section with file-based loading instructions**

Replace lines 11-21 in CLAUDE.md with:

```markdown
## Workflow Checkpoints

**CRITICAL:** At each checkpoint, read the corresponding skill file and follow it exactly.

### File-Based Skill Loading

Claude Code cannot load project-local skills via the Skill tool. Instead, **read skill files directly** using the Read tool:

- **Starting any task:** Read `.claude/skills/vibe-rag-task-workflow.md`
- **Before committing:** Read `.claude/skills/vibe-rag-commit-guidelines.md`
- **Implementing components:** Read `.claude/skills/vibe-rag-tdd.md` + `.claude/skills/vibe-rag-component.md`
- **Writing code:** Read `.claude/skills/vibe-rag-code-quality.md`
- **Handling errors:** Read `.claude/skills/vibe-rag-error-handling.md`
- **Writing docs:** Read `.claude/skills/vibe-rag-documentation.md`
- **Using parallel work:** Read `.claude/skills/vibe-rag-agent-teams.md`

**Important:** These are instructions to Claude Code agents. Read the file, then follow its contents exactly.
```

**Step 3: Verify changes**

Run: Read tool on `CLAUDE.md:11-30` (approximate new range)
Expected: See "Workflow Checkpoints" header and file paths

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
fix: replace Skill tool references with file-based loading

Why this change was needed:
- Claude Code cannot load project-local skills from .claude/skills/
- Skill tool only works with globally registered plugins
- Original /vibe-rag:* skill references were broken

What changed:
- Replaced "Skill-Driven Workflows" with "Workflow Checkpoints"
- Changed skill references from /vibe-rag:name to .claude/skills/vibe-rag-name.md
- Added explanation of file-based loading mechanism
- Instructed Claude to use Read tool instead of Skill tool

Technical notes:
- Tested plugin registration - Claude Code doesn't support project-local plugins
- File-based loading preserves 83.8% context reduction from refactoring
- Skills remain project-scoped and versioned in git
EOF
)"
```

---

## Task 2: Update vibe-rag-task-workflow.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-task-workflow.md:1-9`

**Step 1: Read current skill header**

Run: Read tool on `.claude/skills/vibe-rag-task-workflow.md:1-9`
Expected: See frontmatter and "# vibe-rag Task Workflow" header

**Step 2: Add file-based loading note after frontmatter**

Add after line 6 (after the closing `---`):

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-task-workflow.md`) because Claude Code does not support project-local skill registration.
```

**Step 3: Verify changes**

Run: Read tool on `.claude/skills/vibe-rag-task-workflow.md:1-12`
Expected: See note about file-based loading

**Step 4: Commit**

```bash
git add .claude/skills/vibe-rag-task-workflow.md
git commit -m "$(cat <<'EOF'
docs: add file-based loading note to task-workflow skill

Why this change was needed:
- Clarify that skill is loaded via Read tool, not Skill tool
- Help developers understand why file path is used
- Document limitation of Claude Code skill loading

What changed:
- Added note explaining file-based loading mechanism
- Placed after frontmatter, before main content

Technical notes:
- Consistent with other skill updates
- Does not change skill functionality
EOF
)"
```

---

## Task 3: Update vibe-rag-commit-guidelines.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-commit-guidelines.md:1-9`

**Step 1: Add file-based loading note**

Add after line 6:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-commit-guidelines.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Verify changes**

Run: Read tool on `.claude/skills/vibe-rag-commit-guidelines.md:1-12`

**Step 3: Commit**

```bash
git add .claude/skills/vibe-rag-commit-guidelines.md
git commit -m "docs: add file-based loading note to commit-guidelines skill"
```

---

## Task 4: Update vibe-rag-tdd.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-tdd.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter closing `---`:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-tdd.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-tdd.md
git commit -m "docs: add file-based loading note to tdd skill"
```

---

## Task 5: Update vibe-rag-component.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-component.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-component.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-component.md
git commit -m "docs: add file-based loading note to component skill"
```

---

## Task 6: Update vibe-rag-code-quality.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-code-quality.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-code-quality.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-code-quality.md
git commit -m "docs: add file-based loading note to code-quality skill"
```

---

## Task 7: Update vibe-rag-error-handling.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-error-handling.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-error-handling.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-error-handling.md
git commit -m "docs: add file-based loading note to error-handling skill"
```

---

## Task 8: Update vibe-rag-documentation.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-documentation.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-documentation.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-documentation.md
git commit -m "docs: add file-based loading note to documentation skill"
```

---

## Task 9: Update vibe-rag-agent-teams.md - Add Header Note

**Files:**
- Modify: `.claude/skills/vibe-rag-agent-teams.md:1-9`

**Step 1: Add file-based loading note**

Add after frontmatter:

```markdown

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-agent-teams.md`) because Claude Code does not support project-local skill registration.
```

**Step 2: Commit**

```bash
git add .claude/skills/vibe-rag-agent-teams.md
git commit -m "docs: add file-based loading note to agent-teams skill"
```

---

## Task 10: Update Cross-References in vibe-rag-task-workflow.md

**Files:**
- Modify: `.claude/skills/vibe-rag-task-workflow.md`

**Step 1: Find skill references**

Run: Grep for `/vibe-rag:` in `.claude/skills/vibe-rag-task-workflow.md`
Expected: Find references like `/vibe-rag:tdd`, `/vibe-rag:documentation`

**Step 2: Replace skill references with file reads**

Replace:
- `/vibe-rag:tdd` → "read `.claude/skills/vibe-rag-tdd.md`"
- `/vibe-rag:documentation` → "read `.claude/skills/vibe-rag-documentation.md`"
- `/vibe-rag:commit-guidelines` → "read `.claude/skills/vibe-rag-commit-guidelines.md`"
- `/vibe-rag:agent-teams` → "read `.claude/skills/vibe-rag-agent-teams.md`"

**Step 3: Verify changes**

Run: Grep for `/vibe-rag:` in file
Expected: No matches (all replaced)

**Step 4: Commit**

```bash
git add .claude/skills/vibe-rag-task-workflow.md
git commit -m "$(cat <<'EOF'
fix: update skill cross-references to file-based loading

Why this change was needed:
- Skill tool cannot invoke project-local skills
- Cross-references must use file path instructions
- Consistency with CLAUDE.md file-based loading approach

What changed:
- Replaced /vibe-rag:* references with file path instructions
- Changed "invoke skill" to "read .claude/skills/*.md"
- Updated all cross-references in task-workflow skill

Technical notes:
- Used exact file paths for clarity
- Maintained same workflow semantics
EOF
)"
```

---

## Task 11: Update Cross-References in Other Skills

**Files:**
- Modify: All `.claude/skills/vibe-rag-*.md` files

**Step 1: Search for remaining skill references**

Run: `grep -r "/vibe-rag:" .claude/skills/`
Expected: Find any remaining `/vibe-rag:*` references

**Step 2: Replace each reference**

For each file with references:
- Replace `/vibe-rag:*` with "read `.claude/skills/vibe-rag-*.md`"
- Use Edit tool for exact replacements

**Step 3: Verify all replaced**

Run: `grep -r "/vibe-rag:" .claude/skills/`
Expected: No matches

**Step 4: Commit**

```bash
git add .claude/skills/
git commit -m "fix: update remaining skill cross-references to file paths"
```

---

## Task 12: Test Task Workflow Checkpoint

**Files:**
- Test: CLAUDE.md workflow checkpoint → skill file read

**Step 1: Simulate starting a task**

Action: Read CLAUDE.md, identify "Starting any task" checkpoint
Expected: Find instruction to read `.claude/skills/vibe-rag-task-workflow.md`

**Step 2: Read skill file**

Run: Read tool on `.claude/skills/vibe-rag-task-workflow.md`
Expected: Skill content loads successfully

**Step 3: Verify skill is actionable**

Check: Skill contains clear steps, checklists, examples
Expected: Skill can be followed without Skill tool

---

## Task 13: Test Commit Workflow Checkpoint

**Files:**
- Test: CLAUDE.md workflow checkpoint → skill file read

**Step 1: Simulate commit checkpoint**

Action: Read CLAUDE.md, identify "Before committing" checkpoint
Expected: Find instruction to read `.claude/skills/vibe-rag-commit-guidelines.md`

**Step 2: Read skill file**

Run: Read tool on `.claude/skills/vibe-rag-commit-guidelines.md`
Expected: Skill content with commit message format, examples, checklist

**Step 3: Verify commit format usable**

Check: Can follow commit message format from skill
Expected: Format template, examples, checklist all present

---

## Task 14: Update Design Document with Results

**Files:**
- Modify: `docs/plans/2026-03-01-local-skills-file-based-loading-design.md`

**Step 1: Add Implementation Results section**

Add at end of design doc:

```markdown
## Implementation Results

**Completion Date:** 2026-03-01

### Changes Made

1. **CLAUDE.md:** Replaced "Skill-Driven Workflows" with "Workflow Checkpoints" using file paths
2. **All 8 skill files:** Added file-based loading note in header
3. **Cross-references:** Updated all `/vibe-rag:*` references to file paths
4. **Testing:** Verified all workflow checkpoints work with Read tool

### Validation

- ✅ CLAUDE.md contains file-based loading instructions
- ✅ All skills have header notes explaining file-based loading
- ✅ No broken `/vibe-rag:*` references remain
- ✅ Workflow checkpoints successfully map to skill files
- ✅ Skills are readable and actionable via Read tool
- ✅ Context reduction preserved (83.8%)

### Files Modified

- `CLAUDE.md`
- `.claude/skills/vibe-rag-task-workflow.md`
- `.claude/skills/vibe-rag-commit-guidelines.md`
- `.claude/skills/vibe-rag-tdd.md`
- `.claude/skills/vibe-rag-component.md`
- `.claude/skills/vibe-rag-code-quality.md`
- `.claude/skills/vibe-rag-error-handling.md`
- `.claude/skills/vibe-rag-documentation.md`
- `.claude/skills/vibe-rag-agent-teams.md`
```

**Step 2: Commit design doc update**

```bash
git add docs/plans/2026-03-01-local-skills-file-based-loading-design.md
git commit -m "docs: document implementation results for file-based skill loading"
```

---

## Task 15: Commit Design Document

**Files:**
- Add: `docs/plans/2026-03-01-local-skills-file-based-loading-design.md`

**Step 1: Verify design doc exists**

Run: Read tool on `docs/plans/2026-03-01-local-skills-file-based-loading-design.md`
Expected: Complete design doc with problem, solution, trade-offs

**Step 2: Commit design doc**

```bash
git add docs/plans/2026-03-01-local-skills-file-based-loading-design.md
git commit -m "$(cat <<'EOF'
docs: add design doc for file-based skill loading

Why this change was needed:
- Document investigation of Skill tool limitation
- Explain why file-based loading is the solution
- Provide rationale for future reference
- Guide other projects with same issue

What changed:
- Created comprehensive design document
- Documented Option A (plugin registration) failure
- Documented Option B (file-based loading) success
- Included trade-offs and alternatives considered

Technical notes:
- Tested plugin registration before choosing file-based approach
- File-based loading works immediately with no Claude Code changes
- Preserves all benefits of CLAUDE.md refactoring (83.8% reduction)
EOF
)"
```

---

## Completion Checklist

After all tasks:

- [ ] CLAUDE.md uses file paths instead of skill tool references
- [ ] All 8 skills have file-based loading header notes
- [ ] No broken `/vibe-rag:*` references remain in any file
- [ ] All workflow checkpoints tested and working
- [ ] Design document committed
- [ ] All changes committed with meaningful messages
- [ ] Working tree clean

---

## Success Criteria

✅ Claude Code agents can load local skills via Read tool
✅ All workflow checkpoints map to correct skill files
✅ Skills remain project-scoped and versioned
✅ Context reduction preserved (83.8%)
✅ No dependency on Skill tool for local skills
