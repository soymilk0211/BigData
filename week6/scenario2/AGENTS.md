# AGENTS.md

## Architecture
- Frontend-only web application.
- Use the existing HTML/CSS/JavaScript structure.
- Firebase is used for application data.

## Development rules
- Preserve the current UI structure unless the task requests a redesign.
- Reuse existing modules before creating new abstractions.
- Never commit service-account credentials, private keys, or secrets.
- Do not migrate the project to another framework unless explicitly requested.

## Before finishing
- Check the browser console for errors.
- Verify create/read/update flows against the development Firebase project.
- List changed files and any configuration the user must provide manually.
