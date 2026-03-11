# Advanced GitHub Copilot Exercises

These exercises focus on building an agentic development workflow using custom agents, skills, subagents, and hooks. The weather app codebase is the substrate -- you will build tooling around it, not fix it.

**Time estimate:** Exercises 0-3 fit in a ~2-hour workshop. Exercises 4-7 are stretch goals for continued practice.

**Approach:** These exercises are intentionally open-ended. Discuss design decisions with your group and use Copilot to explore options. There is no single correct solution.

**Prerequisites:** VS Code with GitHub Copilot, agent mode available, enterprise subscription.

---

## Exercise 0: Setup Verification

Before starting, confirm your environment works.

```bash
uv sync
uv run pytest
```

All tests should pass. You do not need an OpenWeatherMap API key for the exercises -- tests mock external calls.

Verify that VS Code agent mode is functional: open the Chat view, check that the agent picker shows both built-in agents (Agent, Plan, Ask, Edit) and that you can switch between them.

Create the directories you will use:

```bash
mkdir -p .github/agents .github/skills .github/hooks
```

---

## Exercise 1: Custom Agent -- Project Manager

**Goal:** Create a custom agent that acts as a project manager for this codebase. It should be able to assess the project, create structured backlog items, and plan features.

**What to build:** An `.agent.md` file in `.github/agents/`.

A custom agent is a Markdown file with YAML frontmatter that defines the agent's name, description, available [tools](https://code.visualstudio.com/docs/copilot/agents/agent-tools), and behavioral instructions. Key frontmatter properties: `description`, `tools`, `model`, `agents`, `handoffs`. See the [file structure reference](https://code.visualstudio.com/docs/copilot/customization/custom-agents#_custom-agent-file-structure).

**Key decisions to make:**
- Which tools should the PM have access to? Consider that it should analyze, not modify.
- What instructions make the PM produce consistent, structured output?
- What should a backlog item look like? (Think: title, description, acceptance criteria, TDD requirements, definition of done.)

**Things to try once the agent exists:**
- Switch to the PM agent and ask it to assess the project and identify improvement areas.
- Ask it to plan a feature it identifies as a good candidate.
- Ask it to review one of its own backlog items for completeness and proper sizing.

**Discussion points:**
- How specific should the instructions be vs. how much should you rely on the model's judgment?
- What [model](https://code.visualstudio.com/docs/copilot/customization/custom-agents#_header-optional) would you choose for this agent and why? Think about cost vs. capability vs. context window.
- How would you test that the agent behaves consistently?

**References:**
- [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [Creating custom agents (GitHub)](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)

---

## Exercise 2: Agent Skills for the PM

**Goal:** Create skills that give the PM agent (and later, other agents) repeatable, deterministic capabilities. Skills are not just instructions -- they include scripts and resources.

**Key concept:** A skill is a directory under `.github/skills/<skill-name>/` with a `SKILL.md` file and optional scripts/resources. The agent loads the skill when it judges the skill relevant, and follows the instructions, which can reference the included scripts. See [SKILL.md file format](https://code.visualstudio.com/docs/copilot/customization/agent-skills#_skillmd-file-format) and [how Copilot uses skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills#_how-copilot-uses-skills).

The difference between a skill and a custom instruction: skills include scripts, examples, and resources alongside instructions. They are loaded on-demand based on relevance, not always-on. They are portable across VS Code, Copilot CLI, and the coding agent. See [skills vs. custom instructions](https://code.visualstudio.com/docs/copilot/customization/agent-skills#_agent-skills-vs-custom-instructions).

**Task:** Think about what the PM agent does repeatedly, and where deterministic scripts would produce more reliable results than the LLM guessing. Discuss with your group and with Copilot. Build at least two skills.

**For each skill:**
- Create the directory structure: `.github/skills/<name>/SKILL.md` plus any scripts.
- The `SKILL.md` must have `name` and `description` in the YAML frontmatter. The `name` must match the directory name.
- Write scripts that produce structured, parseable output. The agent interprets the output; the script ensures deterministic data collection.
- Test the skill by invoking it as a slash command (`/<skill-name>`) or by prompting the PM agent in a scenario where the skill should activate.
- Control visibility with `user-invocable` and `disable-model-invocation` frontmatter properties. See [slash command control](https://code.visualstudio.com/docs/copilot/customization/agent-skills#_use-skills-as-slash-commands).

**Discussion points:**
- What makes a good boundary between "instruction for the agent" and "script that runs deterministically"?
- How do you ensure the agent actually uses the skill vs. trying to do it in its own way?
- Which of these skills would be useful beyond the PM agent?

**References:**
- [Agent skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Creating agent skills (GitHub)](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills)

---

## Exercise 3: Subagent Orchestration -- Feature Implementation Workflow

This is the main exercise. You will design and implement a multi-agent workflow that can take a feature from plan to implementation using TDD.

### 3a: Design the Orchestration

Before writing any agent files, design the workflow as a group. Use the PM agent from Exercise 1 to identify and plan a feature to implement.

Subagents are independent agents that perform focused work and report results back to a main agent. Each runs in its own context window. The main agent waits for results before continuing. Multiple subagents can run in parallel. See [how subagent execution works](https://code.visualstudio.com/docs/copilot/agents/subagents#_how-subagent-execution-works).

**What roles does the workflow need?** Think about separation of concerns: who researches, who writes tests, who writes production code, who documents. Consider:
- Which roles are read-only vs. which need to edit files?
- Which roles can run in parallel?
- What does each role receive as input and what does it return?
- The TDD cycle: someone writes failing tests first, someone else makes them pass.

Use the [coordinator and worker pattern](https://code.visualstudio.com/docs/copilot/agents/subagents#_coordinator-and-worker-pattern) from the docs as a starting point, but adapt it to your needs.

**Design questions to resolve:**
- What information does the coordinator pass to each subagent? What does it expect back?
- Research agents must always return concise, structured summaries -- not dump entire files. How do you enforce this in their instructions?
- What happens when new code conflicts with existing tests? Define the escalation protocol.
- Should each agent use the same model, or would cheaper/faster models work for some roles?
- Do all roles need to be separate agents, or could some be combined?

### 3b: Implement the Agents

Create the agent files in `.github/agents/` based on your design.

Key technical details:
- Agents that should only be invoked as subagents: set [`user-invocable: false`](https://code.visualstudio.com/docs/copilot/agents/subagents#_control-subagent-invocation).
- The coordinator should restrict which subagents it can use via the [`agents` property](https://code.visualstudio.com/docs/copilot/agents/subagents#_restrict-which-subagents-can-be-used-experimental).
- Each agent defines its own `tools` list. Read-only agents should not have edit/terminal tools.
- Worker agents can specify a `model` -- consider cheaper/faster models for narrow tasks.

The coordinator's instructions should define the workflow sequence explicitly: what it delegates first, what it does with the results, what triggers the next step, and what happens on failure.

### 3c: Run a Feature Through It

Take the feature you planned in 3a, switch to the coordinator agent, and give it the feature spec. Observe the full workflow.

**Things to watch for:**
- Does the coordinator actually delegate, or does it try to do everything itself?
- Are the research summaries concise enough, or do they bloat the coordinator's context?
- Does the TDD cycle work -- tests written first, then implementation?
- Does the implementer iterate until tests pass?

**Iterate on the agent instructions based on what you observe.** This is the real work -- the first version will not be perfect.

**References:**
- [Subagents in VS Code](https://code.visualstudio.com/docs/copilot/agents/subagents)
- [Orchestration patterns](https://code.visualstudio.com/docs/copilot/agents/subagents#_orchestration-patterns)

---

## Exercise 4: Refactor the PM Agent (Stretch)

**Goal:** Upgrade the PM agent to use the researcher subagents from Exercise 3 instead of doing its own analysis.

Update the PM agent:
- Add your researcher agents to the `agents` property, and `agent` to the tools list.
- Update the instructions to delegate research to subagents and synthesize the results.
- Optionally add a [handoff](https://code.visualstudio.com/docs/copilot/customization/custom-agents#_handoffs) from the PM to the coordinator: after planning a feature, the user can hand off to the coordinator for implementation.

Test by asking the PM to assess the project. It should delegate the research and produce a more focused assessment.

**Discussion:** How does the PM's output quality change when it gets structured research summaries vs. doing its own ad-hoc file reading?

---

## Exercise 5: Skills Across the Workflow (Stretch)

**Goal:** Identify repeatable operations in the subagent workflow and extract them into skills.

Look at the agents you built in Exercise 3. What do they do repeatedly? Where would a deterministic script produce better results than the LLM improvising? Discuss with your group and with Copilot.

For each skill you identify, create the directory, `SKILL.md`, and any scripts. Then update the relevant agent instructions to reference the skill explicitly (e.g., "Always use the `<skill-name>` skill after modifying source files").

**Discussion:** Skills are loaded based on relevance, not guaranteed to run. How do you increase the likelihood that agents use them? What's the difference between a skill and a hook for enforcing behavior?

---

## Exercise 6: Hooks (Stretch)

**Goal:** Add lifecycle hooks that enforce guarantees the instructions alone cannot.

Create `.github/hooks/` configuration files. Start with one or two hooks and observe their behavior.

Think about the full lifecycle of an agent session and where you want guarantees that instructions alone cannot provide. The available [hook events](https://code.visualstudio.com/docs/copilot/customization/hooks#_hook-lifecycle-events) are: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SubagentStart`, `SubagentStop`, `Stop`.

Hook configuration is JSON in `.github/hooks/`. See [hook configuration format](https://code.visualstudio.com/docs/copilot/customization/hooks#_hook-configuration-format) and [hook input/output](https://code.visualstudio.com/docs/copilot/customization/hooks#_hook-input-and-output) for details on how hooks communicate with the agent.

**Key points:**
- Hooks run deterministically -- they are shell commands, not LLM suggestions. An instruction that says "always format" is a suggestion. A hook that formats is a guarantee.
- A `Stop` hook that blocks must check `stop_hook_active` to prevent infinite loops.
- [Agent-scoped hooks](https://code.visualstudio.com/docs/copilot/customization/hooks#_agent-scoped-hooks) (defined in the agent's frontmatter `hooks` field) only run when that agent is active. Requires `chat.useCustomAgentHooks` to be enabled.
- `PreToolUse` hooks can [control tool approval](https://code.visualstudio.com/docs/copilot/customization/hooks#_pretooluse-output): allow, deny, or ask.

**Discussion:** Where is the line between "the agent should decide" and "the system must enforce"? What are the risks of hooks that block agent operations?

**References:**
- [Hooks in VS Code](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [Using hooks (GitHub)](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/use-hooks)

---

## Exercise 7: MCP Server Integration (Stretch / Discussion)

**Goal:** Identify where Model Context Protocol servers could extend the agents' capabilities.

This exercise is primarily a design discussion. MCP servers expose external tools to agents via a standardized protocol. Think about what tools your agents lack that could be provided by an MCP server.

**Discussion prompts:**
- The PM agent creates backlog items as text. What if it could create GitHub Issues directly? (The GitHub MCP server can do this.)
- The implementer runs tests via terminal. What if test results were available as a structured MCP tool with parsed output?
- Could the weather API itself be exposed as an MCP tool for integration testing?
- What would a "project metrics" MCP server look like -- one that exposes code complexity, test coverage, and dependency audit as tools?

**If time permits:** Configure an existing MCP server (e.g., the GitHub MCP server) in one of your agents using the `mcp-servers` property in the agent frontmatter, and try using it.
