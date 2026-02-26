---
name: using-linear
description: Use when working with Linear tickets/issues - establishes workflows for creating and updating tickets (issues)
---

## Accessing Linear

Use your Bash tool to call the `linearis` executable for communicating with Linear. Prior to your first use of `linearis` you must run `linearis usage` once to learn how to use it.

## Creating issues and sub-issues

If it's not clear which project a new ticket belongs to, stop and ask the user. When creating sub-issues, use the parent ticket's project.

## Working on issues

The return values of the `issues` commands contain an `embeds` array which holds the URLs of the screenshots, documents, etc. that are part of the ticket description. If a ticket or comment contains such embeds, and they seem relevant to the ticket, fetch and view them as well. Use local caching when needed.

## Writing Ticket Bodies And Comments (Required)
- You must ask the user for confirmation before writing a ticket description or comment.
- Whenever posting a ticket description or comment, **do not** inline the body text.
- First write the content to a file using a heredoc, then pass the file to `linearis` as needed.
- Always prefix the body with a first, standalone paragraph: `(This is from an LLM)`
- Ensure all bodies/comments are Markdown with clear logical structure: short intro, headings, and concise lists. Avoid walls of text.

## Eagerness

Never declare "Implementation Complete!" in a ticket unless explicitly told so.
