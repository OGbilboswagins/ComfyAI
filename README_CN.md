中文 ｜ [English](./README.md)

<div align="center">

# 🎯 ComfyUI-Copilot: ComfyUI 智能助手

<h4 align="center">

<div align="center">
<img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="版本"> 
<img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可证">
<img src="https://img.shields.io/github/stars/AIDC-AI/ComfyUI-Copilot?color=yellow" alt="星标">
<img src="https://img.shields.io/github/issues/AIDC-AI/ComfyUI-Copilot?color=red" alt="问题">
<img src="https://img.shields.io/badge/python-3.10%2B-purple.svg" alt="Python">

</h4>

👾 _**阿里巴巴国际数字商业集团**_ 👾

<p align="center">
          :octocat: <a href="https://github.com/AIDC-AI/ComfyUI-Copilot"><b>Github</b></a>&nbsp&nbsp | &nbsp&nbsp 💬 <a href="https://github.com/AIDC-AI/ComfyUI-Copilot/blob/main/assets/qrcode.png"><b>微信</b></a>&nbsp&nbsp
</p>

</div>

https://github.com/user-attachments/assets/0372faf4-eb64-4aad-82e6-5fd69f349c2c

## 🌟 介绍

说到 AI 绘画界的瑞士军刀，ComfyUI 绝对可以 C 位出道。这个强大的开源生图工具，提供了低代码形式的AI算法调试和部署能力，能够快速生成文本、图像、音频等丰富内容。让你的「闲置显卡」瞬间变成艺术工坊，实在是甲方看了沉默、美工看了流泪...
但！是！
当一上头打开了 ComfyUI 界面，往往会遭受灵魂暴击：
❌ 报错提示比摩斯密码还难懂
❌ 节点连线比蜘蛛网还复杂
❌ 参数调整比女朋友的心思还难猜
❌ 好不容易求到了大佬的工作流文件，打开后发现：
<div align="center">
<img src="assets/broken_workflow_funny.png" width="30%">
</div>

让**ComfyUI-Copilot** 来拯救你！让你用自然语言对话就能在ComfyUI中完成AI生图开发，新手5分钟上手，老手效率翻倍！

为你枯燥繁琐的ComfyUI工作流搭建、工作流Debug、工作流优化和迭代过程，全程保驾护航！ComfyUI-Copilot 提供直观的工作流生成、工作流Debug、工作流调优修改、批量参数跑图探索和各项辅助工作流搭建手段（节点推荐和介绍、模型推荐、下游子图推荐），堪称ComfyUI界的cursor。
相比上一个版本，从协助您完成工作流开发过程，到代替您完成开发过程，ComfyUI-Copilot 已经从辅助工具升级为工作流开发助手。以下是v2.0新增核心功能：
* 新增了工作流Debug功能，能够自动分析工作流中的错误，并提供修复建议
* 新增了工作流改写功能，可以根据您的描述，优化当前工作流结构，修改参数新增节点
* 优化了AI工作流生成能力，能够根据您的需求，生成符合您需求的工作流
* 架构升级为了mcp结构，可感知您本地ComfyUI的环境安装情况，从而给出最优的解决方案

<div align="center">
<img src="assets/Framework.png"/>
</div>

---

## 🔥 核心功能（V2.0.0）

- 1. 💎 **生成第一版工作流**：根据您的文字描述，给到符合您需求的工作流，返回3个我们库里的优质工作流和1个AI生成的工作流，您可以一键导入到ComfyUI中，开始生图
  - 直接在输入框输入：我想要一个xxx的工作流
  <img src="assets/工作流生成.gif"/>
- 2. 💎 **工作流Debug**：自动分析工作流中的错误，帮您修复参数错误和工作流连接错误，并给出优化建议
  - 上方返回的4个工作流里，当您选中了一个点击Accept后，会导入ComfyUI的画布中。此时您可以点击Debug按钮，开始调错。
  - 输入框右上角有一个Debug按钮，点击后直接对当前的画布上的工作流进行Debug。
  <img src="assets/debug.gif"/>
- 3. 💎 **之前的工作流生图效果不满意？**：提出您不满意的地方，让我们帮您修改工作流，增加节点，修改参数，优化工作流结构
  - 在输入框输入：帮我在当前的画布上添加一个xxxx
  <img src="assets/改写.gif"/>
- 4. 💎 **调参过程太痛苦？**：我们为您提供了调参工具，您可以设置参数范围，系统会自动批量执行不同参数组合，并生成结果可视化对比，帮助您快速找到最优参数配置
  - 切换Tab到GenLab，然后根据引导使用，请注意此时的工作流要能正常运行，才能批量跑图评估参数。
  <img src="assets/GenLab.gif"/>

想让ComfyUI-Copilot辅助您完成工作流开发？
- 5. 💎 **节点推荐**：根据您的描述，推荐您可能需要的节点，并给出推荐理由
  - 在输入框输入：我想要一个xxx的工作流
<img src="assets/节点推荐.gif"/>

- 6. 💎 **节点查询系统**：选中画布上的节点，点击节点查询按钮，深入探索节点，查看其说明、参数定义、使用技巧和下游工作流推荐。
  - 在输入框输入：我想要一个用来干xxx的节点
<img src="assets/节点信息查询.gif"/>

- 7. 💎 **模型推荐**：根据您文字需求， Copilot 为您查找基础模型和 'lora'。
  - 在输入框输入：我想要一个生成xxx图片的Lora
<img src="assets/模型推荐.gif"/>

- 8. 💎 **下游节点推荐**：在您选中了画布上的某个节点后，根据您画布上已有的节点，推荐您可能需要的下游子图
<img src="assets/下游节点推荐.gif"/>

---

## 🚀 快速开始

**仓库概览**：访问 [GitHub 仓库](https://github.com/AIDC-AI/ComfyUI-Copilot) 以获取完整代码库。

#### 内测版本的安装
目前只支持通过git来安装。

  1. 用git把ComfyUI-Copilot的mcp分支安装到ComfyUI的custom_nodes目录下：

   ```bash
   cd ComfyUI/custom_nodes
   git clone git@github.com:AIDC-AI/ComfyUI-Copilot.git
   或
   cd ComfyUI/custom_nodes
   git clone https://github.com/AIDC-AI/ComfyUI-Copilot
   * 至此main分支就已经安装好了

   git fetch origin mcp
   git checkout -b mcp origin/mcp
   git pull
   * 至此mcp分支就下载好了

   ```

  2. 在ComfyUI的custom_nodes目录下，找到ComfyUI-Copilot目录，安装ComfyUI-Copilot的依赖

   ```bash
   cd ComfyUI/custom_nodes/ComfyUI-Copilot
   pip install -r requirements.txt
   ```
   如果您是windows用户：

   ```bash
   python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\ComfyUI-Copilot\requirements.txt
   ```
   

  3. （待后续支持） **使用 ComfyUI 管理器**：打开 ComfyUI 管理器，点击自定义节点管理器，搜索 ComfyUI-Copilot，并点击安装按钮。
   <img src="assets/comfyui_manager.png"/>
   <img src="assets/comfyui_manager_install.png"/>


#### **激活**
在运行 ComfyUI 项目后，在面板左侧找到 Copilot 激活按钮以启动其服务。
<img src="assets/start.jpg"/>

#### **API Key 生成**
点击*按钮，在弹窗里输入您的电子邮件地址，API Key 将稍后自动发送到您的电子邮件地址。收到API Key后，将API Key粘贴到输入框中，点击保存按钮，即可激活Copilot。
<img src="assets/keygen.png"/>

#### **注意**：
本项目持续更新中，请更新到最新代码以获取新功能。您可以使用 git pull 获取最新代码，或在 ComfyUI Manager 插件中点击“更新”。
我们的项目依赖于一些外部接口，服务部署在新加坡，可能需要您使用科学上网工具哦。

---

## 🤝 贡献

我们欢迎任何形式的贡献！可以随时提出 Issues、提交 Pull Request 或建议新功能。


## 📞 联系我们

如有任何疑问或建议，请随时联系：ComfyUI-Copilot@service.alibaba.com。

Discord 社群：
<div align="center">
<img src='assets/discordqrcode.png' width='300'>
</div>

微信服务群：
<div align="center">
<img src='https://github.com/AIDC-AI/ComfyUI-Copilot/blob/main/assets/qrcode.png' width='300'>
</div>

## 📚 许可证

该项目采用 MIT 许可证 - 有关详情，请参阅 [LICENSE](https://opensource.org/licenses/MIT) 文件。

## ⭐ 星标历史

[![星标历史图](https://api.star-history.com/svg?repos=AIDC-AI/ComfyUI-Copilot&type=Date)](https://star-history.com/#AIDC-AI/ComfyUI-Copilot&Date)
