# 图片理解功能实现

## 概述

本次更新为 ComfyUI-Copilot 的 MCP 客户端添加了图片理解能力，参考了 reference 实现中的图片处理逻辑。

## 主要变更

### 1. MCP 客户端 (`backend/service/mcp-client.py`)

- 添加了 `ImageData` 类用于封装图片数据
- 修改了 `comfyui_agent_invoke` 函数签名，支持接收图片参数
- 实现了多模态输入处理，将文本和图片组合成 OpenAI Vision API 格式
- 增强了 Agent 指令，添加了图片分析相关的引导

```python
class ImageData:
    """Image data structure to match reference implementation"""
    def __init__(self, filename: str, data: str, url: str = None):
        self.filename = filename
        self.data = data  # base64 data
        self.url = url    # uploaded URL

async def comfyui_agent_invoke(prompt: str, images: List[ImageData] = None):
    # 支持图片输入的处理逻辑
```

### 2. API 控制器 (`backend/controller/conversation_api.py`)

- 添加了图片数据处理逻辑，包括 base64 解码和 OSS 上传
- 实现了 `upload_to_oss` 函数（当前为本地存储的简化版本）
- 修改了 `invoke_chat` 函数，支持将图片数据传递给 MCP 客户端

```python
# 处理图片上传到OSS
processed_images = []
if images and len(images) > 0:
    for image in images:
        # 解码base64数据，上传到OSS，创建ImageData对象
        processed_image = ImageData(filename, data, url)
        processed_images.append(processed_image)

# 传递给MCP客户端
async for result in comfyui_agent_invoke(prompt, processed_images):
    # 处理响应
```

## 功能特性

1. **多模态输入支持**: 支持同时处理文本和图片输入
2. **图片格式兼容**: 支持 PNG, JPG, JPEG, GIF, WebP 等常见格式
3. **OSS 集成**: 预留了 OSS 上传接口，当前实现为本地存储
4. **错误处理**: 完善的错误处理机制，单个图片处理失败不影响其他图片
5. **向后兼容**: 保持对纯文本输入的完全兼容

## 使用方式

### 前端调用

前端已经支持图片上传，通过 `workflowChatApi.ts` 中的 `streamInvokeServer` 函数：

```typescript
const response = await WorkflowChatAPI.streamInvokeServer(
    sessionId, 
    prompt, 
    uploadedImages.map(img => img.file), // 图片文件数组
    intent,
    ext,
    traceId
);
```

### 后端处理流程

1. 接收前端发送的 base64 图片数据
2. 解码并上传到 OSS（或本地存储）
3. 创建 `ImageData` 对象
4. 传递给 MCP 客户端进行处理
5. 返回包含图片分析结果的响应

## 测试

使用提供的测试脚本验证功能：

```bash
cd backend/service
python test_image_support.py
```

## 待完善功能

1. **真实 OSS 集成**: 当前使用本地存储，需要集成真实的 OSS 服务
2. **图片缓存**: 实现图片缓存机制，避免重复上传
3. **图片压缩**: 添加图片压缩功能，优化传输效率
4. **批量处理**: 优化多图片批量处理性能

## 与 Reference 实现的对比

本实现参考了 reference 中的以下关键特性：

1. **图片预处理**: 类似于 reference 中的图片上传到 OSS 逻辑
2. **多模态消息格式**: 使用与 reference 相同的 OpenAI Vision API 格式
3. **错误处理**: 采用了 reference 中的错误处理模式
4. **配置传递**: 保持了与 reference 相同的配置传递方式

## 注意事项

- 确保使用支持视觉功能的模型（如 gpt-4o, gpt-4o-mini）
- 图片大小限制：建议小于 5MB
- 支持的图片格式：PNG, JPG, JPEG, GIF, WebP 