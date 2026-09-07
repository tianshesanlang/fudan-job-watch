# 复旦招聘监测台 Fudan Job Watch

自动循检复旦大学官方招聘信源，优先捕获 **外国语言文学学院**、**大学英语教学部** 以及全校教学科研 / 博士后岗位。新出现的高优先岗位会推送到 Grok 通知、邮箱、Notion 与 GitHub Issue。

## 看板

- 仓库看板：[index.html](./index.html)（可直接打开，已嵌入种子数据）
- GitHub Pages：[https://tianshesanlang.github.io/fudan-job-watch/](https://tianshesanlang.github.io/fudan-job-watch/)
  - 若 404：仓库 Settings → Pages → Source 选 **GitHub Actions**
- Notion 库：[复旦招聘监测](https://app.notion.com/p/a5f0a30bd4404af58b3cb001fb9e0b1f)

## 监测源（官方优先）

| 源 | 栏目 | 地址 |
| --- | --- | --- |
| 外国语言文学学院 | 通知公告 | https://dfll.fudan.edu.cn/27751/list.htm |
| 大学英语教学部 | 通知公告 | https://cec.fudan.edu.cn/23080/list.htm |
| 人事处 | 教学科研 | https://hr.fudan.edu.cn/15364/list.htm |
| 人事处 | 博士后 | https://hr.fudan.edu.cn/15369/list.htm |
| 人事处 | 教辅 / 党政 / 思政 / 派遣制 | hr.fudan.edu.cn 对应栏目 |
| 人才招聘系统 | 官方申报入口 | https://zp.fudan.edu.cn （需登录，无法公开抓取） |

微信公众号（无法稳定抓取，请手动关注）：**复旦大学**、**复旦人事**、**复旦大学英语教学部**。

## 推送节奏

| 通道 | 频次 |
| --- | --- |
| GitHub Actions `monitor.yml` | 每日 08:00 / 20:00（上海）抓取，高优先新岗开 Issue |
| Grok Automation 「复旦招聘每日监测」 | 每日 08:00（上海）循检官网，写入 Notion，邮箱 + App 通知 |
| Notion 库 | 去重后的岗位台账 |

## 优先级

- **高-对口**：外文学院 / 大英部的教师、博士后、教学科研招聘
- **中-相关**：全校岗位但涉及语言、翻译、国际交流、区域国别
- **低-其他**：其余教学科研 / 博士后 / 派遣制（备查）

通常要求 **博士学历**，线上申报 [zp.fudan.edu.cn](https://zp.fudan.edu.cn)。外文学院联系人郑老师 `fdwwhr@fudan.edu.cn` / `021-65642690`（以最新公告为准）。

## 本地跑一次

```bash
python3 scripts/scrape.py
```

## 当前重点

外文学院 **教师招聘启事** 截止 **2026-12-31**：助理教授 B 岗，法 / 韩 / 西 / 日文系。大英部通知公告暂无教师招聘，仍会定时循检。
