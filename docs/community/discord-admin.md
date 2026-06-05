# Discord Server Setup & Admin Instructions

This document provides step-by-step instructions for the project owner to create and configure the official Wright Discord server.

## 1. Server Creation

1. Open Discord and click the **Add a Server** (+) button.
2. Select **Create My Own** -> **For a club or community**.
3. Set the Server Name to `Wright` and upload the official logo as the server icon.

---

## 2. Channel Architecture

Create the following channels and configure their permissions exactly as specified below:

| Channel Name | Category | Permissions / Rules |
| :--- | :--- | :--- |
| `#announcements` | Welcome | Read-only for members (only Admins can post). Used for release notes, breaking changes, and project milestones. |
| `#rules` | Welcome | Read-only for members. Contains the community guidelines. |
| `#general` | Discussion | Open discussion about Wright, AI, and mechanical engineering. |
| `#support` | Help | Help with installation, configuration, and usage. Cross-link to GitHub Discussions for complex issues. |
| `#contributing` | Development | Discussion for contributors (PRs, feature ideas, architecture questions). |
| `#showcase` | Community | Share projects built with Wright (images, CAD files, screenshots). |
| `#off-topic` | Casual | Non-Wright related general conversations. |

---

## 3. Invites & Discoverability

### Generating a Permanent Invite Link
1. Hover over `#general` or `#announcements` and click **Create Invite**.
2. Click **Edit invite link** (gear icon).
3. Set **Expire After** to `Never`.
4. Set **Max Number of Uses** to `No limit`.
5. Click **Generate a New Link** and copy the link.
6. Place this permanent link in:
   - `README.md`
   - `CONTRIBUTING.md`
   - `SUPPORT.md`
   - Documentation site navigation config

---

## 4. Safety & Moderation Settings

To protect the server from spam and maintain a high-quality community environment, configure these safety features in Server Settings:

*   **Verification Level**: Set to **Medium** (Must be registered on Discord for longer than 5 minutes).
*   **Explicit Media Content Filter**: Set to **Scan media content from all members**.
*   **AutoMod Rules**:
    *   Enable **Block Commonly Flagged Words** to prevent offensive language.
    *   Enable **Block Spam Content** to auto-flag links and excessive mentions.
