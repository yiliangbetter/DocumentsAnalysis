# Claude Code Project Guidelines

## Git Commit Workflow

**Rule: Create a git commit after every meaningful step.**

### When to Commit

Create a commit after completing:

1. **New Features**
   - Adding a new API endpoint
   - Implementing a new UI component
   - Adding a new utility function
   - Setting up a new service or module

2. **Bug Fixes**
   - Fixing a runtime error
   - Correcting logic issues
   - Resolving type errors
   - Fixing broken tests

3. **Refactoring**
   - Improving code organization
   - Extracting reusable components
   - Simplifying complex functions

4. **Configuration & Setup**
   - Adding dependencies
   - Updating configuration files
   - Setting up testing infrastructure

### Commit Message Format

```
<type>: <short description>

[optional longer description]

please do not use Co-Authored-By
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config, etc.)

### Examples

```bash
# After implementing a new feature
feat: add document upload endpoint with PDF support

# After fixing a bug
fix: correct chunking logic to preserve sentence boundaries

# After adding tests
test: add unit tests for document processor

# After refactoring
refactor: extract text extraction into separate module
```

### Commit Checklist

Before committing, verify:

- [ ] The code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] The change is complete and self-contained
- [ ] Commit message follows the format above
- [ ] No sensitive data is included (API keys, passwords, etc.)

### Workflow

1. Make focused, incremental changes
2. Test the changes work as expected
3. Stage the relevant files (`git add`)
4. Create commit with descriptive message
5. Continue to next task

Remember: **Small, frequent commits are better than large, infrequent ones.**

## Project-Specific Notes

### Backend Tests

```bash
cd backend
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run test:coverage
```

### Running the Application

```bash
# Terminal 1 - Backend
cd backend && uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend && npm run dev
```
