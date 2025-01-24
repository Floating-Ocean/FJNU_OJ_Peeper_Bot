<h1 align="center">FJNU_OJ_Peeper_Bot(Nonebot Branch)</h1>
<div align="center">
  <strong>基于PBG项目和官方接口的QQ机器人</strong><br>
</div><br>

<div align="center">
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/actions/workflows/codeql.yml"><img alt="CodeQL Scan" src="https://img.shields.io/github/actions/workflow/status/Floating-Ocean/FJNU_OJ_Peeper_Bot/codeql.yml?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/commits"><img alt="GitHub Last Commit" src="https://img.shields.io/github/last-commit/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
  <a href="https://github.com/Floating-Ocean/FJNU_OJ_Peeper_Bot/commits"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/y/Floating-Ocean/FJNU_OJ_Peeper_Bot?style=flat-square"></a>
</div>

# 开始之前：

本分支由 [qwedc001](https://github.com/qwedc001) 维护。请注意，此分支与主项目完全不同，主项目是一个经过配置后可以独立运行的 **官方 QQ 机器人**，而本分支是一个 **Nonebot 机器人**。

这意味着，本分支的代码不会直接运行，而是需要在 **Nonebot** 环境下运行。如果你不了解 **Nonebot**，请先阅读 [Nonebot 文档](https://nonebot.cqp.moe/)。

同时，本分支下的具体代码实现可能会与主项目产生差异。但整体功能追求和主分支大概一致。

本分支的配置主要集中于 src/core/constants.py 下。

分支维护者正在使用 FastAPI 通过反向 WS 以实现 Napcat 与 Nonebot 的通信。通信采用 Onebot V11 标准。
