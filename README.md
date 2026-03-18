# engineering-news-to-wechat

A reusable OpenClaw skill for turning a structured engineering-news Markdown digest into a WeChat Official Account draft via the official API.

## What it does

This skill packages a repeatable workflow for:

1. preparing a structured Markdown engineering-news digest,
2. validating Markdown → HTML locally with a dry run,
3. uploading a cover image,
4. converting the article into WeChat-safe HTML,
5. uploading the result into the WeChat draft box.

It is designed for recurring workflows such as:
- daily engineering news digests,
- regional + national industry briefings,
- scheduled “write Markdown first, publish to draft later” pipelines.

## Scope

This repository focuses on the **draft-upload pipeline**.

It does **not**:
- auto-publish to a public WeChat article,
- generate article content from scratch,
- generate cover images,
- bundle private notification targets or personal IDs,
- read secrets from checked-in config files.

## Requirements

Set credentials through environment variables:

```bash
export WX_APPID='your_appid'
export WX_APPSECRET='your_appsecret'
```

## Repository layout

```text
engineering-news-to-wechat/
├── SKILL.md
├── README.md
├── references/
│   ├── cron-examples.md
│   ├── markdown-template.md
│   └── wechat_api.md
└── scripts/
    ├── dry_run_publish.py
    ├── get_token.py
    ├── md_to_html.py
    ├── run_daily_pipeline.sh
    ├── upload_draft.py
    ├── upload_img.py
    └── upload_thumb.py
```

## Quick start

Prepare a Markdown article and a local cover image, then run:

```bash
bash scripts/run_daily_pipeline.sh \
  --article /path/to/article.md \
  --cover /path/to/cover.png \
  --title "2026-03-18 工程圈晚报" \
  --author "小瞎子" \
  --digest "一句话摘要"
```

If successful, the script prints:
- article path,
- generated HTML path,
- thumbnail media ID,
- WeChat draft media ID.

## Markdown shape

A typical article looks like this:

```md
# 2026-03-18 工程圈晚报

这里写导语。

## 国内工程圈十件大事

1. **标题一**
   1-2 句摘要。
   来源：<https://example.com/1>

## 湖南工程圈十件大事

1. **标题一**
   1-2 句摘要。
   来源：<https://example.com/2>

结语：今天无高价值新增。
```

The renderer in this repo already handles multi-line list items safely for the WeChat draft flow.

## Scheduling

For recurring jobs, a practical pattern is:
- main job at a fixed time, e.g. 19:00,
- retry / inspection job 20 minutes later if the main run fails.

See:
- `references/cron-examples.md`

## Skill usage

For OpenClaw usage details, see:
- `SKILL.md`

## Notes

- Prefer official and high-authority sources.
- De-duplicate similar updates before writing.
- If there is not enough high-value news on a given day, explicitly write: `今天无高价值新增`.
