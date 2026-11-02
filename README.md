# takashiyoshino.random-walk.org

Takashi Yoshino の個人サイトのソースです。[Quarto](https://quarto.org) で作り、GitHub Pages で公開しています。

## 書き方

- 記事は `posts/<日付>-<名前>/index.qmd` に Markdown で書きます。数式は `$...$` と `$$...$$`。
- `main` に push すると、数分後にサイトに反映されます（`.github/workflows/publish.yml`）。
- 業績の一覧（`_publications.md`）は、描画のたびに `scripts/orcid.py` が ORCID から作り直します。手で編集しません。ORCID の更新は、週に一度の自動実行でも反映されます。

## 手元で見る

```sh
quarto preview
```
