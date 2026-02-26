Help me review this GitHub pull request and also give me a pedagogical scaffolded understanding of the system context, overall data flow, and the problem being solved. I do not want to just review the PR; I want to understand its place in the system.

Use independent sub-agents as needed. Use `$jujutsu` for VCS. When finished, run a final independent sub-agent to iteratively review your work until both of you are satisfied. Ensure final work is coherent and logically structured. Remember that you have access to a `web.run` tool to find citations if helpful. Use the plan/todo tool to track tasks.

---

Keep an incrementally updated doc in `{{DOC_OUTPUT_PATH}}` up to date with what you have reviewed, how, why, conclusions so far, and next steps using Markdown checklists. Ensure final analysis is prepended at the top. When an independent sub-agent finishes, represent its thoughts, conclusions, and artifacts incrementally in the doc for that specific sub-agent with specific findings and evidence. When referencing files, try to use GitHub Markdown links for GitHub repositories.

{{PR_URL}}

Important service code to take into consideration is available cloned in the `~/workplace` directory and the current working directory.

---

Use `$use-gh-cli` to get description and comments. Then use `$using-linear` to get the associated Linear issue if possible, and from that issue get related Linear issues, projects, and additional context. For related Linear issues, find their GitHub pull requests and get description/comments for deeper context. For Linear issues, also fetch issue comments.

Once confident you understand the context of the problem, analyze the PR.

Pay close attention to existing comments and comment threads in the PR under review. Analyze responses from the author. In the current PR diff, are comments that claim to address issues actually substantiated by code? State whether you agree and why.
