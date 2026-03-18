---
name: engineering-news-to-wechat
description: Generate a structured engineering news Markdown digest, validate Markdown→HTML locally, then upload it to WeChat Official Account draft box via official API. Use when the user wants a repeatable “行业快报/工程圈晚报 → Markdown → 微信公众号草稿箱” workflow, including scheduled daily runs, dry-run validation, and retry-friendly publishing.
---

# Engineering News to WeChat

把“结构化行业快报”收敛成一个可重复执行的 skill：
- 先整理新闻为 Markdown
- 再本地 dry-run 验证 Markdown → HTML
- 最后上传到微信公众号草稿箱

适合：
- 工程圈晚报
- 行业十件大事
- 区域 + 全国双板块日报
- 需要 cron 定时执行的微信公众号草稿链路

不适合：
- 自动 publish 到公众号
- 自动生成封面图
- 凭空捏造新闻来源
- 依赖私有 openid / 私聊通知目标的封装发布

## 输入要求

执行前至少明确：
- Markdown 输出路径
- 封面图路径
- 文章标题
- 作者（可选）
- digest（可选，<= 120 字）

环境变量：

```bash
export WX_APPID='...'
export WX_APPSECRET='...'
```

## 标准工作流

### 1. 先生成 Markdown

推荐固定结构：
- 标题
- 导语
- `## 国内工程圈十件大事`
- `## 湖南工程圈十件大事`（或其他地区板块）
- 结语

每条建议包含：
- 标题
- 1-2 句摘要
- 来源链接

如果当天缺少足够高质量新增，明确写：`今天无高价值新增`。

### 2. 再做 dry-run

```bash
python3 scripts/dry_run_publish.py article.md
```

如果 dry-run 失败，不要继续上传。

### 3. 转 HTML + 上传草稿

```bash
THUMB_ID=$(python3 scripts/upload_thumb.py cover.png)
python3 scripts/md_to_html.py article.md > /tmp/article.html
python3 scripts/upload_draft.py \
  --title "2026-03-18 工程圈晚报" \
  --html /tmp/article.html \
  --thumb-media-id "$THUMB_ID" \
  --author "小瞎子" \
  --digest "一句话摘要"
```

### 4. 向用户回报

至少说明：
- Markdown 文件路径
- 是否上传成功
- 草稿 `media_id`
- 若失败，明确阻塞点

## 推荐写作约束

- 优先官方来源、权威媒体、公司/项目官方博客、GitHub 官方仓库、正式公告
- 避免低质量聚合站、镜像站、重复内容
- 同类信息先去重再写
- 不要为了凑数硬塞低质量条目

## 列表排版规则（重要）

本 skill 的 `md_to_html.py` 已兼容以下常见写法，会自动把列表项的后续缩进行折叠进同一个条目：

```md
1. **标题**
   第一段内容。
   第二段内容。
   来源：<https://example.com>
```

所以正常写多行列表项即可，不必手工压成单行。

## 推荐的自动化方式

如果要做每日自动执行，建议：
- 主任务：固定时间生成 Markdown + 上传草稿
- 兜底任务：20 分钟后巡检；若失败则自动补跑一次

把“生成内容”和“补跑兜底”分成两个 cron，比把所有逻辑硬塞进一个任务更稳。

## 参考文件

需要查微信公众号 API 或上传限制时，读：
- `references/wechat_api.md`

如果要走统一入口脚本，执行：
- `scripts/run_daily_pipeline.sh`
