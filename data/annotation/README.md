# Annotation workspace (local only)

This directory holds annotation batches and adjudication files. They are
**not committed** because they contain evaluation data and may still carry
indirect personal information.

Workflow:

1. `python scripts/export_annotation_batch.py` creates two independent batches:
   `batch_all_a.csv` and `batch_all_b.csv`.
2. Each annotator fills only the `label` column with one of the seven classes.
3. `python scripts/merge_annotations.py --a ... --b ...` computes Cohen's kappa.
4. Disagreements go to `disagreements.csv` for a third annotator.
5. After adjudication, save `id,text,split,label` to a file and pass it with
   `--adjudicated`.
6. The merged `data/processed/human_verified.csv` is used as validation/test.

Do not share `key_*.csv` with annotators: it contains the weak labels and can
bias the annotation.
