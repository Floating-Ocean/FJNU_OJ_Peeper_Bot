<h1 align="center">FJNU_OJ_Peeper_Bot</h1>
<div align="center">
  <strong>基于PBG项目和官方接口的QQ机器人</strong><br>
</div><br>

<div align="center">
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/actions/workflows/codeql.yml"><img alt="CodeQL Scan" src="https://img.shields.io/github/actions/workflow/status/Floating-Ocean/FJNU_OJ_Peeper_Bot/codeql.yml?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/commits"><img alt="GitHub Last Commit" src="https://img.shields.io/github/last-commit/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/commits"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/y/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
</div>

## 开始之前

本仓库包含主项目和一个分支，主项目是一个经过配置后可以独立运行的 **官方 QQ 机器人**，而分支则是一个 **Nonebot 机器人**。

请在运行机器人前，将 [`config_example.json`](https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/blob/main/config_example.yaml) 重命名为 `config.json`，并根据文件内提示填写相关字段。

[>> 前往 **Nonebot** 侧开发分支](https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/tree/dev-nonebot)

## Bot 能做什么

- 基于 [`Peeper-Board-Generator`](https://github.com/qwedc001/Peeper-Board-Generator) 项目的 [`FJNUACM Online Judge`](https://fjnuacm.top/) 榜单爬取以及用户信息获取；
- 面向 [`Codeforces`](https://codeforces.com/) 平台的随机选题、用户信息获取、提交记录查询、比赛查询、基于 [`Carrot`](https://github.com/meooow25/carrot) 浏览器插件项目的比赛表现实时预估；
- 面向 [`AtCoder`](https://atcoder.jp/) 平台的随机选题（基于 [`Clist`](https://clist.by/) 平台接口）、用户信息获取、比赛查询；
- 面向 [`NowCoder`](https://ac.nowcoder.com/) 平台的用户信息获取、比赛查询；
- 基于 [`Uptime Robot`](https://uptimerobot.com/) 的多个算法竞赛平台可用性查询；
- 基于 [`Hitokoto`](https://hitokoto.cn/) 的一言获取；
- 基于 [`Random.org`](https://www.random.org/) 的真随机数功能；

<br>

- 表情包的分类管理、添加、审核、随机；
- 在中国传统颜色中随机色卡；
- 给定指令生成二维码图片；

<br>

- PRs Welcome
