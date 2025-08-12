[中文](./README_CN.md) ｜ English

<div align="center">

# 🎯 ComfyUI-Copilot: Your Intelligent Assistant for Comfy-UI

<!-- Enhancing Image Generation Development with Smart Assistance -->

<h4 align="center">

<div align="center">
<img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version"> 
<img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
<img src="https://img.shields.io/github/stars/AIDC-AI/ComfyUI-Copilot?color=yellow" alt="Stars">
<img src="https://img.shields.io/github/issues/AIDC-AI/ComfyUI-Copilot?color=red" alt="Issues">
<img src="https://img.shields.io/badge/python-3.10%2B-purple.svg" alt="Python">

</h4>


👾 _**Alibaba International Digital Commerce**_ 👾

:octocat: [**Github**](https://github.com/AIDC-AI/ComfyUI-Copilot)

</div>

https://github.com/user-attachments/assets/0372faf4-eb64-4aad-82e6-5fd69f349c2c

## 🌟 Introduction

When it comes to the Swiss Army knife of AI art generation, ComfyUI absolutely deserves the spotlight. This powerful open-source image generation tool provides low-code AI algorithm debugging and deployment capabilities, enabling rapid generation of rich content including text, images, and audio. It transforms your "idle graphics card" into an instant art workshop, truly leaving clients speechless and designers in tears...

But! Here's the catch!

When you enthusiastically open the ComfyUI interface, you're often hit with a soul-crushing reality:
❌ Error messages more cryptic than Morse code
❌ Node connections more complex than spider webs  
❌ Parameter adjustments harder to figure out than your girlfriend's mood
❌ Finally getting a workflow file from an expert, only to open it and find:
<img src="assets/broken_workflow_funny.png">

Let **ComfyUI-Copilot** save you! Use natural language conversations to complete AI image generation development in ComfyUI - beginners can get started in 5 minutes, experts can double their efficiency!

ComfyUI-Copilot provides comprehensive support for your tedious ComfyUI workflow building, workflow debugging, workflow optimization and iteration processes! It offers intuitive workflow generation, workflow debugging, workflow tuning and modification, batch parameter exploration, and various auxiliary workflow building tools (node recommendations and introductions, model recommendations, downstream subgraph recommendations), making it the Cursor of the ComfyUI world.

Compared to the previous version, ComfyUI-Copilot has evolved from assisting you in workflow development to replacing you in the development process, upgrading from an auxiliary tool to a workflow development assistant.

Whether it's generating text, images, or audio, ComfyUI-Copilot offers intuitive node recommendations, workflow building aids, and model querying services to streamline your development process.

Compared to the previous version, ComfyUI-Copilot has evolved from assisting you in workflow development to replacing you in the development process, upgrading from an auxiliary tool to a workflow development assistant. Here are the core new features of v2.0:
* Added workflow Debug functionality that can automatically analyze errors in workflows and provide repair suggestions
* Added workflow rewriting functionality that can optimize current workflow structure and modify parameters to add nodes based on your description
* Optimized AI workflow generation capability that can generate workflows that meet your needs based on your requirements
* Architecture upgraded to MCP structure, which can perceive your local ComfyUI environment installation status to provide optimal solutions

<div align="center">
<img src="assets/Framework.png"/>
</div>

---

## 🔥 Core Features (V2.0.0)

- 1. 💎 **Generate First Version Workflow**: Based on your text description, we provide workflows that meet your needs, returning 3 high-quality workflows from our library and 1 AI-generated workflow. You can import them into ComfyUI with one click to start generating images.
  - Simply type in the input box: I want a workflow for xxx
  <img src="assets/工作流生成.gif"/>
- 2. 💎 **Workflow Debug**: Automatically analyze errors in workflows, help you fix parameter errors and workflow connection errors, and provide optimization suggestions.
  - Among the 4 workflows returned above, when you select one and click Accept, it will be imported into the ComfyUI canvas. At this time, you can click the Debug button to start debugging.
  - There is a Debug button in the upper right corner of the input box. Click it to directly debug the workflow on the current canvas.
  <img src="assets/debug.gif"/>
- 3. 💎 **Unsatisfied with Previous Workflow Results?**: Tell us what you're not satisfied with, and let us help you modify the workflow, add nodes, modify parameters, and optimize workflow structure.
  - Type in the input box: Help me add xxx to the current canvas
  <img src="assets/改写.gif"/>
- 4. 💎 **Parameter Tuning Too Painful?**: We provide parameter tuning tools. You can set parameter ranges, and the system will automatically batch execute different parameter combinations and generate visual comparison results to help you quickly find the optimal parameter configuration.
  - Switch to the GenLab tab and follow the guidance. Note that the workflow must be able to run normally at this time to batch generate and evaluate parameters.
  <img src="assets/GenLab.gif"/>

Want ComfyUI-Copilot to assist you in workflow development?
- 5. 💎 **Node Recommendations**: Based on your description, recommend nodes you might need and provide recommendation reasons.
  - Type in the input box: I want a workflow for xxx
<img src="assets/节点推荐.gif"/>

- 6. 💎 **Node Query System**: Select a node on the canvas, click the node query button to explore the node in depth, view its description, parameter definitions, usage tips, and downstream workflow recommendations.
  - Type in the input box: I want a node for xxx
<img src="assets/节点信息查询.gif"/>

- 7. 💎 **Model Recommendations**: Based on your text requirements, Copilot helps you find base models and 'lora'.
  - Type in the input box: I want a Lora that generates xxx images
<img src="assets/模型推荐.gif"/>

- 8. 💎 **Downstream Node Recommendations**: After you select a node on the canvas, based on the existing nodes on your canvas, recommend downstream subgraphs you might need.
<img src="assets/下游节点推荐.gif"/>

---

## 🚀 Getting Started

**Repository Overview**: Visit the [GitHub Repository](https://github.com/AIDC-AI/ComfyUI-Copilot) to access the complete codebase.

#### Installation
  1. Use git to install ComfyUI-Copilot in the ComfyUI custom_nodes directory:

   ```bash
   cd ComfyUI/custom_nodes
   git clone git@github.com:AIDC-AI/ComfyUI-Copilot.git
   ```
   
   or
   
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/AIDC-AI/ComfyUI-Copilot
   ```

  2. In the ComfyUI custom_nodes directory, find the ComfyUI-Copilot directory and install ComfyUI-Copilot dependencies

   ```bash
   cd ComfyUI/custom_nodes/ComfyUI-Copilot
   pip install -r requirements.txt
   ```
   If you are a Windows user:

   ```bash
   python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\ComfyUI-Copilot\requirements.txt
   ```
   

  3. (To be supported later) **Using ComfyUI Manager**: Open ComfyUI Manager, click on Custom Nodes Manager, search for ComfyUI-Copilot, and click the install button.
   <img src="assets/comfyui_manager.png"/>
   <img src="assets/comfyui_manager_install.png"/>

#### **Activation**
After running the ComfyUI project, find the Copilot activation button on the left side of the panel to launch its service.
<img src="assets/start.jpg"/>

#### **API Key Generation**
Click the * button, enter your email address in the popup window, and the API Key will be automatically sent to your email address later. After receiving the API Key, paste it into the input box, click the save button, and you can activate Copilot.
<img src="assets/keygen.png"/>

#### **Note**：
This project is continuously updated. Please update to the latest code to get new features. You can use git pull to get the latest code, or click "Update" in the ComfyUI Manager plugin.

---

## 🤝 Contributions

We welcome any form of contribution! Feel free to make issues, pull requests, or suggest new features.

---

## 📞 Contact Us

For any queries or suggestions, please feel free to contact: ComfyUI-Copilot@service.alibaba.com.
<div align="center">
  <img src="assets/qrcode.png" width="20%"/> 
   
  WeChat
  
  <img src="assets/discordqrcode.png" width="20%"/>
  
  Discord
</div>


## 📚 License

This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/licenses/MIT) file for details.

---
## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=AIDC-AI/ComfyUI-Copilot&type=Date)](https://star-history.com/#AIDC-AI/ComfyUI-Copilot&Date)

