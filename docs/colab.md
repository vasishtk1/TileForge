# Running TileForge on Colab

Colab provides the GPU. Its machine is wiped when a session ends, so the setup cells run at the
start of every session (about 30 seconds). The notebook itself lives in this repo.

## Each session

1. Open the notebook:
   https://colab.research.google.com/github/vasishtk1/TileForge/blob/main/notebooks/colab_train.ipynb
   (or click "Open in Colab" in the README).
2. **Runtime → Change runtime type → T4 GPU** (if not already selected).
3. **Runtime → Run all.**
4. Check the last cell's output shows `CUDA available: True` and a GPU name.

To get code changes onto Colab: push from your Mac, then re-run the setup cell (it runs
`git pull`).

## What survives a session

| Thing | Survives? | Where it lives |
|---|---|---|
| Code | Yes | GitHub |
| Notebook | Yes | GitHub |
| Installed packages | No | Re-installed by the setup cell |
| Datasets, checkpoints | Not yet | Will be saved to Google Drive (set up in Week 1) |

## Troubleshooting

- **`nvidia-smi: command not found`** or `CUDA available: False`: the runtime has no GPU.
  Change the runtime type and run all again.
- **"Cannot connect to GPU backend"**: the free tier's GPU quota is used up. Wait a few hours or
  try again later.
- **Edits made in Colab are lost**: don't edit code in Colab. Edit on your Mac and push.
