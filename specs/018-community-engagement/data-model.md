# Data Model: Contributor Recognition Schema

This document details the configuration model of the `.all-contributorsrc` JSON file used to track community contributions.

## Contributor Recognition Schema (.all-contributorsrc)

The root configuration file is a structured JSON document.

### JSON Schema

```json
{
  "projectName": "wright",
  "projectOwner": "burhop",
  "repoType": "github",
  "repoHost": "https://github.com",
  "files": [
    "README.md"
  ],
  "imageSize": 100,
  "commit": false,
  "contributorsPerLine": 7,
  "contributors": [
    {
      "login": "username",
      "name": "Full Name",
      "avatar_url": "https://avatars.githubusercontent.com/u/...",
      "profile": "https://github.com/username",
      "contributions": [
        "code",
        "doc",
        "design"
      ]
    }
  ],
  "contributorsSortBy": "contributions"
}
```

### Fields Description

| Field | Type | Description |
| :--- | :--- | :--- |
| `projectName` | String | The name of the project repository (`wright`). |
| `projectOwner` | String | The owner's GitHub organization or username (`burhop`). |
| `repoType` | String | Hosting type (`github`). |
| `repoHost` | String | URL of the repository hosting provider. |
| `files` | Array | Files containing the contributors table that will be auto-updated. |
| `imageSize` | Number | Height and width of contributor avatars in pixels (default: `100`). |
| `commit` | Boolean | Whether to auto-commit changes made by the CLI (default: `false` to review changes). |
| `contributorsPerLine` | Number | Maximum number of avatars shown per table row (default: `7`). |
| `contributors` | Array | List of tracked contributors. |
| `contributorsSortBy` | String | The sorting criteria for rendering the contributors list (e.g. `contributions`). |

### Contributor Object Fields

| Sub-field | Type | Description |
| :--- | :--- | :--- |
| `login` | String | The contributor's GitHub username. |
| `name` | String | The contributor's full name. |
| `avatar_url` | String | URL to the contributor's avatar image. |
| `profile` | String | Link to the contributor's website or GitHub profile. |
| `contributions` | Array | Types of contributions (e.g., `code`, `doc`, `design`, `ideas`, `bug`, `review`). |
