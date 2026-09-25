---
name: frontend-review
description: Conducts an automated architectural and UI-integration code review on recent git changes in the frontend against React production standards.
tools: ['read', 'grep', 'glob', 'bash']
---

# Frontend Code Review Skill

This skill performs a rigorous code review of recently added or modified React code. It acts as a senior frontend reviewer ensuring that the implementation strictly adheres to modern React practices (Hooks, Functional Components), separation of concerns (encapsulated API calls), proper loading/error states, and strict ESLint/Prettier formatting before code is merged.

## Inputs

- **Target Code:** Recent git commits (`git diff HEAD~1`), staged changes (`git diff --cached`), or specific files modified in the `frontend/` directory.
- **Context Files:** `.github/copilot-instructions.md`, `.github/instructions/react-standards.md`, and `TASK.md`.

## When NOT to use

- Do not use when modifying backend Python files, database migrations, or infrastructure configs.
- Do not use for initial empty project skeletons that contain no UI components.

## Steps

1. **Load Standards:** Review the rules defined in `.github/instructions/react-standards.md`.
2. **Analyze Changes:** Run `git diff` or inspect the modified `.js` and `.jsx` files in `frontend/src/` to understand the scope of the UI implementation.
3. **Architecture & State Check:**
   - Verify that ONLY Functional Components and React Hooks (`useState`, `useEffect`) are used.
   - Verify that components do not contain raw `fetch()` or `axios` calls directly inside them. All API logic MUST be extracted to a dedicated service (e.g., `services/api.js`).
4. **UX & Error Handling Check:**
   - Ensure that asynchronous operations (like uploading PDFs or waiting for the RAG AI response) have explicit loading states (disabling buttons, showing spinners).
   - Verify that backend HTTP errors (400, 422) are caught and displayed as user-friendly UI messages, not raw console dumps.
5. **Formatting & Linter Check:**
   - Run the frontend quality commands via bash to ensure no formatting or linter issues were introduced:
     ```bash
     cd frontend && npx prettier --check "src/**/*.{js,jsx,css}"
     cd frontend && npx eslint "src/**/*.{js,jsx}" --max-warnings 0
     ```
   - Flag any formatting discrepancies or ESLint warnings/errors as blocking issues.
6. **Generate Report:** Produce a structured Markdown review report summarizing the findings.

## Output Format

```markdown
## Frontend Code Review Report — [Increment Name / Branch]

### Blocking Issues (Must Fix)
- [File/Line]: [Description of architectural violation, e.g., raw fetch in UI component, missing loading state, or direct DOM manipulation]
- [File/Line]: [ESLint or Prettier failure description]

### Recommendations (Nice to Have)
- [File/Line]: [Suggestion for better component splitting, CSS modularity, or prop naming]

### Quality Verification
- [ ] Code is formatted with Prettier and passes ESLint with 0 warnings.
- [ ] API calls are properly encapsulated in service files.
- [ ] Async actions have proper loading and error handling states.

### Verdict: [PASS / CHANGE REQUESTED]
[Brief concluding summary of the UI implementation quality]
```

## Rules
- Zero Tolerance for Fat Components: Immediately flag any UI component that mixes raw ```fetch()``` calls or heavy data-transformation logic inside the render block or ```onClick``` handlers.
- No Legacy React: Flag any use of Class Components or legacy lifecycle methods (e.g., ```componentDidMount```) as blocking issues.
- No Direct DOM Manipulation: Instantly flag any use of ```document.getElementById```, ```querySelector```, or similar vanilla JS DOM methods. ```useRef``` and state must be used instead.
- Strict Verdicts: If there is even one "Blocking Issue" or if ESLint fails, the Verdict MUST be ```CHANGE REQUESTED```. Only issue a ```PASS``` if all React, UX, and linter constraints are met.
- Actionable Feedback: Always explain why something is wrong and provide a brief snippet showing the correct modern React pattern (e.g., how to move the fetch call to a service).
