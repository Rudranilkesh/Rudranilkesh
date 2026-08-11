# GitHub Profile Stats — Setup

## 1. Put these files in `Rudranilkesh/Rudranilkesh`

Copy the contents of this package into your profile repository.

## 2. Create the `GHT` secret

The analytics generator needs a GitHub token with `read:user`. If you want private-repository data included, also grant the appropriate `repo` access.

GitHub → `Rudranilkesh/Rudranilkesh` → Settings → Secrets and variables → Actions → New repository secret

- Name: `GHT`
- Value: your GitHub token

Do not put the token inside README.md or the workflow.

## 3. Enable write permissions

Repository → Settings → Actions → General → Workflow permissions → **Read and write permissions**.

## 4. Run it once

Actions → **Update GitHub Profile Stats** → Run workflow.

After a successful run, these local SVGs are committed into `profile/`:

- `profile.svg` — GitHub analytics
- `top-langs.svg` — top languages by repository code
- `language.svg` — top languages by commit changes
- `streak.svg` — contribution streak
- `trophy.svg` — GitHub trophies
- `heatmap.svg` — contribution heatmap
- `timedist.svg` — commit time distribution

The README references these local files, so it no longer depends on live image URLs for these cards.
