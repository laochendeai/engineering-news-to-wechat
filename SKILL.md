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
  --author "弱电陈工" \
  --digest "一句话摘要"
```

### 4. 向用户回报

至少说明：
- Markdown 文件路径
- 是否上传成功
- 草稿 `media_id`
- 若失败，明确阻塞点

## 微信推荐写作规则（必读）

写完文章后对照检查，确保符合以下规则。**文中不得出现 SEO/GEO 字样**，优化分析在回复中单独汇报。

### 钩子开头（最重要）
- 前100字必须让读者觉得"这篇对我有用"
- 像短视频文案一样：直接给价值、制造好奇、点明痛点
- ❌ 不要铺垫背景、不要"今天我们来聊聊"
- ✅ "这篇文章梳理了XX的N个关键点，XX可以直接打印自查清单用"

### 完读率优先
- 日报1500-2500字，专题2000-4000字
- 段落不超过4-5行（手机适配）
- 每500字放一个锚点（小标题/加粗句/表格/清单）
- 日报控制在5-6条，每条200-300字
- "弱电人怎么看"控制在2句话以内

### 结构规范
- H2标题下不超过3个H3，不超过3层嵌套
- 关键结论加粗，读者只看加粗部分也能获得核心信息
- 善用表格（对比/排查）和清单（步骤/要点）
- 不要用长引用块、大段代码、过多 `---` 分隔线

### 标题
- 15-30字
- 包含数字+场景/人群
- 避免纯品牌词、过于抽象、无信息量

### 封面图
- 尺寸900×383px（2.35:1）
- 深色底+亮色字，在浅色列表中跳出
- 文字少而精（最多2行），字号大
- 内容与标题一致

### 结尾
- 必须有互动引导（提问/征集/预告下一篇）
- 日报有"一句话总结"给出行动指引

### 互动引导示例
- "你在万兆项目中遇到过什么坑？评论区聊聊"
- "这周你关注哪个展会？留言告诉我"
- "明天我们聊XX，关注不迷路"

### 发布时间
- 工作日：7:30-8:30 / 12:00-13:00 / 18:00-19:30
- 周末：9:00-10:30 / 20:00-22:00

### 负反馈信号（必须避免）
- 标题党（标题与内容不符）
- 广告硬植入
- 低质量转载/洗稿
- 文中包含 SEO/GEO 等技术术语

详细推荐机制参考：`references/wechat-recommend-rules.md`

## 连续内容规则（重要）

- 文章结尾预告了下一篇主题 → **必须立即写下一篇并推送到草稿箱**
- 不要等老陈提醒，形成内容链条（如：施工工艺→报价漏项→合同陷阱→进场条件）
- 如果当前会话被中断，把"待写下一篇：XXX"写入当日 memory 文件，下次会话继续
- 默认作者：**弱电陈工**

## 内容来源约束

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
