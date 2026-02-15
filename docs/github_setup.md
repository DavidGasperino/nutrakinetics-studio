# GitHub Setup

## Current state

- Local repo initialized
- Initial commit created on `main`
- Remote set to:
  - `git@github.com-personal:DavidGasperino/nutrakinetics-studio.git`
- New SSH key generated:
  - private: `~/.ssh/github_personal_ed25519`
  - public: `~/.ssh/github_personal_ed25519.pub`

## 1) Add SSH key to GitHub account

1. Copy public key:

```bash
cat ~/.ssh/github_personal_ed25519.pub
```

2. In GitHub UI, go to:

- Settings -> SSH and GPG keys -> New SSH key
- Title: `nutrakinetics-studio-local`
- Paste key and save

## 2) Create repository on GitHub

Create an empty repository named `nutrakinetics-studio` under account `DavidGasperino` (no README/.gitignore/license during creation).

## 3) Push

```bash
cd /Users/davidgasperino/workspace/SupplementO/nutrakinetics-studio
git push -u origin main
```

## Optional: move project to `/Users/davidgasperino/workspace`

If you want it outside `SupplementO`, move and keep git history:

```bash
mv /Users/davidgasperino/workspace/SupplementO/nutrakinetics-studio \
   /Users/davidgasperino/workspace/nutrakinetics-studio
```
