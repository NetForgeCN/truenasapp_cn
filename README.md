# TrueNAS 应用中文选型手册

把应用商店的英文清单整理成可检索、可筛选的中文选型页面，并通过 GitHub Pages 直接访问。

网站地址：https://netforgecn.github.io/truenasapp_cn/

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `raw_apps.txt` | **英文原始清单**。每 4~5 行一条：来源、名称、星标（可选）、版本、英文简介。这是唯一需要日常维护的源文件。 |
| `data/translations.json` | 中文详解库。按应用名称保存分类、定位、功能、适用场景、安装提示、难度与资源估计。 |
| `scripts/generate.py` | 生成脚本。合并英文清单与中文详解库，输出 `index.html`。 |
| `index.html` | 生成的单文件页面，由 GitHub Pages 提供访问。请勿手工编辑，它会被自动生成覆盖。 |
| `.github/workflows/regenerate.yml` | 自动化流程。源文件变动后自动生成并提交 `index.html`。 |

## 日常更新

### 1. 更新英文清单

直接编辑 `raw_apps.txt` 后提交到 `main` 分支。GitHub Actions 会自动运行生成脚本，更新 `index.html`；无需手动执行任何命令。

格式示例（星标可选）：

```
community
应用名称
1234
1.2.3
One-line English description.

community
没有星标的应用
1.0.0
Another English description.
```

### 2. 新增应用

如果新增的应用在中文详解库中没有对应条目，生成脚本会自动用英文简介生成基础介绍，并在页面上标注"新增应用 · 中文详解待补充"，页面不会出错。

之后补充中文详解即可，有两种方式：

- **手工补充**：在 `data/translations.json` 中按现有格式增加一条，字段包括 `name`、`source`、`version`、`category`、`tagline`、`what_it_is`、`features`、`use_case`、`tips`、`difficulty`、`resources`。
- **交给 AI 补充**：把更新后的 `raw_apps.txt` 发给 AI，让它生成新增应用的中文详解并追加到 `data/translations.json`。

提交后自动化流程会重新生成页面。

### 3. 本地生成（可选）

```bash
python3 scripts/generate.py
```

无需安装任何第三方依赖，Python 3.8+ 即可。

## 页面功能

- 按名称、定位、功能、场景搜索
- 按分类、来源（community / stable / enterprise）、难度、资源筛选
- 按热度、名称、分类、上手难度排序
- 勾选候选应用并导出 CSV 清单（选择会保存在浏览器本地）
- 打印或导出 PDF，排版已针对打印优化

## 说明

中文详解是基于英文清单简介与项目常识整理的选型概述，不是官方文档；具体能力、依赖与授权条款请以各项目官方说明为准。
