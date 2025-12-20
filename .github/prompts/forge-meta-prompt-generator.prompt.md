---
description: Generate a new prompt file following Copilot best practices
agent: 'agent'
---

# Prompt File Generator

## Purpose

This meta-prompt generates well-structured prompt files based on your objectives while automatically following GitHub Copilot best practices. It analyzes your requirements and creates a complete, ready-to-use prompt file with proper structure, variables, validation steps, and context references.

The generated prompt will be automatically saved to the `.prompts-generated` folder.

## How to Use

1. Run this prompt from VS Code chat
2. Answer the questions about your objective
3. The prompt file will be automatically created in .prompts-generated/
4. Review and test the generated file
5. Move it to your desired location when ready

## User Objective

Describe what you want to accomplish with the new prompt:

**Task description:**
${input:taskDescription:Describe what this prompt should accomplish (e.g., "Generate React components with tests" or "Create database migrations with rollback")}

**Target audience:**
${input:targetAudience:Who will use this prompt? (e.g., "frontend team", "all developers", "personal use")}

**Expected output:**
${input:expectedOutput:What should this prompt produce? (e.g., "TypeScript component files and test files" or "API documentation in Markdown")}

## Analysis

Based on the objective, analyze:
1. What agent mode is most appropriate? (agent, ask, edit, or custom agent name)
2. Should tools be restricted? (only specify if you want to limit available tools, otherwise omit)
3. Should a specific model be recommended? (only specify if task requires specific model capabilities, otherwise omit)
4. What variables should be included for dynamic inputs?
5. What context should be referenced? (files, tools, codebase)

## File Creation Instructions

After generating the prompt structure below, create the actual file:

1. Create the `.prompts-generated` directory if it does not exist
2. Generate a descriptive filename in kebab-case (e.g., `database-migration.prompt.md`)
3. Save the complete prompt file to `.prompts-generated/[filename].prompt.md`
4. Confirm the file was created successfully

**Important:** Base all specifics in the generated prompt on what the user provides in their inputs. Do not assume:
- Specific project structures or file locations
- Particular tech stacks or frameworks
- Standard commands or build tools
- Coding standards or conventions

Only include these details if the user explicitly provides them in the task description, expected output, or context.

## Generated Prompt Structure

Create a complete prompt file with the following structure:

### 1. YAML Frontmatter
```yaml
---
description: [One-sentence description of what this prompt does]
agent: [agent mode: 'agent', 'ask', 'edit', or custom agent name]
tools: [only include if you need to restrict tools - omit for default access]
model: [only include if task requires specific model - omit to let user choose]
---
```

**Note:** Only include `tools` if you want to limit available tools (e.g., read-only prompts). Only include `model` if the task requires specific model capabilities (e.g., vision processing, advanced reasoning). Otherwise omit both for flexibility.

### 2. Prompt Title and Context
- Clear title describing the task
- Brief context explaining the purpose
- Reference to any relevant project standards or patterns

### 3. Input Variables
Define all necessary variables using this format:
```
Variable name: ${input:variableName:Descriptive prompt for user}
```

Include variables for:
- Core inputs required for the task
- Optional configuration parameters
- Target locations or file patterns

### 4. Requirements Section
List specific requirements based on the user's task description:
```markdown
## Requirements

1. **Requirement Category:** Description based on user's needs
   - Specific detail from user input
   - Another specific detail

2. **Another Category:** Description relevant to the task
   - Details here
```

Cover areas relevant to the user's task, which may include:
- Technical requirements (if specified by user)
- Code quality standards (if mentioned by user)
- Testing requirements (if applicable to the task)
- Documentation needs (if part of expected output)
- Performance considerations (if relevant to the task)

**Note:** Only include requirement categories that are relevant to the specific task the user described. Do not assume generic requirements unless they apply to the stated objective.

### 5. Expected Output
Clearly define what files or artifacts should be created based on user's requirements:
```markdown
## Expected Output

1. Create file: `path/to/file.ext` (use paths from user's description)
2. Update file: `path/to/existing.ext` (if applicable)
3. Generate documentation: `docs/filename.md` (if applicable)
```

**Important:** Use file paths and structures that match what the user described in their task description. Do not assume specific directory structures unless provided.

### 6. Code Examples or Patterns
If applicable, include examples showing:
- Expected code structure
- Good vs. bad patterns
- Specific syntax or conventions

Use this format:
```markdown
## Examples

**Good:**
```language
// Example of good implementation
```

**Avoid:**
```language
// Example of what not to do
```
```

### 7. Context References
Include references to relevant context as provided by the user:
- Related files: `#file:path/to/file` (only if user provides file paths)
- Tools to use: `#tool:toolName`
- Codebase search: `#codebase`
- Similar patterns: Search instructions

Example:
```markdown
## Context

Follow the patterns in #file:src/components/Example.tsx
Search for similar implementations: #tool:search pattern-name
```

**Note:** Only include specific file references if the user has provided them in the task description or context.

### 8. Validation Steps
Define how to verify success based on the task requirements:
```markdown
## Validation Steps

After generation:
1. Run `command` - expected result (use commands appropriate to the task)
2. Check for [specific criteria relevant to the output]
3. Verify [another criteria based on requirements]
4. Manual test: [specific steps if applicable]
```

**Note:** Validation commands and steps should be appropriate to the user's described task and environment. Do not assume specific build tools or commands unless the user mentioned them.

### 9. Additional Notes (Optional)
Include relevant considerations based on the task:
- Edge cases to consider
- Common pitfalls to avoid
- Performance tips (if relevant to the task)
- Security considerations (if relevant to the task)

**Note:** Only include notes that are relevant to the specific task. Base these on the user's described requirements, not on assumed project standards.

## Best Practices to Apply

Ensure the generated prompt follows these principles:

1. **User-Driven Content:** Base all specific details on what the user provides - do not assume project structures, tech stacks, or conventions
2. **Specificity:** Be precise about requirements, avoid vague instructions
3. **Self-Contained:** Include all necessary context and instructions
4. **Clear Variables:** Use descriptive variable names and helpful prompts
5. **Actionable Requirements:** Provide specific, testable requirements
6. **Success Criteria:** Define clear validation steps
7. **Context Rich:** Reference relevant files, tools, and patterns that the user has provided
8. **Example Driven:** Show concrete examples of expected output
9. **Scoped Appropriately:** Match task complexity to agent mode choice
10. **Minimal Configuration:** Only specify tools or model when necessary to restrict or require specific capabilities

## Output Format

Create the complete prompt file and save it to the .prompts-generated directory.

**File location:** `.prompts-generated/[descriptive-name].prompt.md`

**Filename format:** Use kebab-case ending in .prompt.md (e.g., `react-component-generator.prompt.md`, `api-endpoint-crud.prompt.md`)

After creating the file:
1. Confirm the file has been saved
2. Provide the file path
3. Summarize what the prompt does
4. Give brief usage instructions

## Example Generation

For a task like "Generate a new React component with tests", you should:
1. Analyze the requirements and determine appropriate settings
2. Generate a complete prompt file with:
   - Variables for component name, props, and functionality
   - Requirements for TypeScript, testing, and documentation
   - References to patterns (only if user provided them)
   - Clear file structure expectations based on user's description
   - Validation steps including test runs and type checking
   - Examples of component structure
3. Save the file to `.prompts-generated/react-component.prompt.md`
4. Confirm creation and provide usage instructions

The generated prompt should enable users to consistently accomplish the stated objective.

Remember: After generating the prompt structure, you must actually create the file in the .prompts-generated directory. Base all specific details on what the user provides in their inputs.