# takashiyoshino.random-walk.org

Takashi Yoshino の個人サイトのソースです。[Quarto](https://quarto.org) で作り、GitHub Pages で公開しています。

## 書き方

- 記事は `posts/<日付>-<名前>/index.qmd` に Markdown で書きます。数式は `$...$` と `$$...$$`。
- 講義ノートは `lectures/<講義>/<番号>-<名前>/index.qmd` に書きます（例：`lectures/katachi/06-variational/`）。
  - 並び順はフォルダ名の番号で決まります（`01-`, `02-`, …）。講義の目次（`lectures/<講義>/index.qmd`）、サイドバー、前後の回へのリンクは自動で作られます。
  - 新しい講義を足すときは、`_quarto.yml` の `sidebar:` に `id` と `contents: lectures/<講義>` を足します。
  - 今はすべて `draft: true` です。公開するときは、その回と講義の目次と `lectures/index.qmd` の `draft: true` を外し、`_quarto.yml` のナビバーの Lectures の行のコメントを外します。
- `main` に push すると、数分後にサイトに反映されます（`.github/workflows/publish.yml`）。
- 業績の一覧（`_publications.md`）は、描画のたびに `scripts/orcid.py` が ORCID から作り直します。手で編集しません。ORCID の更新は、週に一度の自動実行でも反映されます。

## 手元で見る

```sh
quarto preview
```
