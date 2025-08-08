// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { Message } from "../../types/types";
import { UserMessage } from "./messages/UserMessage";
import { AIMessage } from "./messages/AIMessage";
// Import as components to be used directly, not lazy-loaded
import { LoadingMessage } from "./messages/LoadingMessage";
import { generateUUID } from "../../utils/uuid";
import { app } from "../../utils/comfyapp";
import { addNodeOnGraph } from "../../utils/graphUtils";
import { lazy, Suspense, useEffect, useLayoutEffect, useRef, useState } from "react";
import Showcase from "./messages/Showcase";
import { useChatContext } from "../../context/ChatContext";

// Define types for ext items to avoid implicit any
interface ExtItem {
  type: string;
  data?: any;
}

interface NodeMap {
    [key: string | number]: any;
}

interface NodeWithPosition {
    id: number;
    type: string;
    pos: [number, number];
}

const enum LoadMoreStatus {
    USED = 'used',
    NOT_USED = 'not_used'
}
interface LoadMoreButtonProps {
    id?: string
    buttonType?: 'loadmore';
    buttonStatus?: LoadMoreStatus
}

interface MessageListProps {
    messages: Message[];
    onOptionClick: (option: string) => void;
    latestInput: string;
    installedNodes: any[];
    onAddMessage: (message: Message) => void;
    onUpdateMessage: (message: Message) => void;
    loading?: boolean;
    isActive?: boolean;
}

const getAvatar = (name?: string) => {
    return `https://ui-avatars.com/api/?name=${name || 'User'}&background=random`;
};

type FinallyMessageProps = Message | LoadMoreButtonProps

// Use lazy loading for components that are conditionally rendered
const LazyWorkflowOption = lazy(() => import('./messages/WorkflowOption').then(m => ({ default: m.WorkflowOption })));
const LazyNodeSearch = lazy(() => import('./messages/NodeSearch').then(m => ({ default: m.NodeSearch })));
const LazyDownstreamSubgraphs = lazy(() => import('./messages/DownstreamSubgraphs').then(m => ({ default: m.DownstreamSubgraphs })));
const LazyNodeInstallGuide = lazy(() => import('./messages/NodeInstallGuide').then(m => ({ default: m.NodeInstallGuide })));
const LazyDebugGuide = lazy(() => import('./messages/DebugGuide').then(m => ({ default: m.DebugGuide })));
const LazyDebugResult = lazy(() => import('./messages/DebugResult').then(m => ({ default: m.DebugResult })));

// 默认显示3轮回答，也就是找到列表最后的3条role是ai的数据
const DEFAULT_COUNT = 3;

export function MessageList({ messages, latestInput, onOptionClick, installedNodes, onAddMessage, onUpdateMessage, loading, isActive }: MessageListProps) {
    const { isAutoScroll } = useChatContext()

    const [currentIndex, setCurrentIndex] = useState<number>(0)
    const [currentMessages, setCurrentMessages] = useState<FinallyMessageProps[]>([])
    const scrollRef = useRef<HTMLDivElement>(null)
    const lastMessagesCount = useRef<number>(0)
    const currentScrollHeight = useRef<number>(0) 
    const isLoadHistory = useRef<boolean>(false)
    
    // 用于跟踪已经处理过的工作流和参数更新，防止重复执行
    const processedUpdates = useRef<Set<string>>(new Set())
    
    // 当消息列表发生重大变化时（如清除消息、切换会话），清空已处理的更新记录
    useEffect(() => {
        // 如果消息数量大幅减少（比如清除消息），清空处理记录
        if (messages.length < processedUpdates.current.size / 2) {
            processedUpdates.current.clear();
        }
    }, [messages]);

    // 关联用户消息和AI响应的checkpoint信息
    const processMessagesWithCheckpoints = (messages: Message[]): Message[] => {
        const processedMessages = [...messages];
        
        for (let i = 0; i < processedMessages.length; i++) {
            const message = processedMessages[i];
            
            // 检查AI消息是否包含checkpoint信息
            if ((message.role === 'ai' || message.role === 'tool') && message.content) {
                try {
                    const response = JSON.parse(message.content);
                    if (response.ext) {
                        // 查找修改前的checkpoint信息（给用户消息）
                        const checkpointExt = response.ext.find((item: any) => 
                            item.type === 'workflow_rewrite_checkpoint' || 
                            (item.type === 'debug_checkpoint' && item.data?.checkpoint_type === 'workflow_rewrite_start')
                        );
                        
                        // 查找修改后的版本信息（保留在AI响应中）
                        const completeExt = response.ext.find((item: any) => 
                            item.type === 'workflow_rewrite_complete'
                        );
                        
                        // 如果找到修改前的checkpoint，将其关联到前一条用户消息
                        if (checkpointExt && i > 0) {
                            const prevMessage = processedMessages[i - 1];
                            if (prevMessage.role === 'user') {
                                // 为用户消息添加修改前的checkpoint信息
                                processedMessages[i - 1] = {
                                    ...prevMessage,
                                    ext: [checkpointExt]
                                };
                            }
                        }
                        
                        // 如果找到修改后的版本信息，保留在AI响应中，并移除修改前的checkpoint
                        if (completeExt) {
                            // 从AI响应中移除修改前的checkpoint，只保留修改后的版本信息
                            const updatedResponse = { ...response };
                            updatedResponse.ext = response.ext.filter((item: any) => 
                                item.type !== 'workflow_rewrite_checkpoint' && 
                                !(item.type === 'debug_checkpoint' && item.data?.checkpoint_type === 'workflow_rewrite_start')
                            );
                            
                            // 更新AI消息内容
                            processedMessages[i] = {
                                ...message,
                                content: JSON.stringify(updatedResponse)
                            };
                        }
                    }
                } catch (error) {
                    // 忽略JSON解析错误
                }
            }
        }
        
        return processedMessages;
    };
    
    useEffect(() => {
        const el = scrollRef.current
        if (!el) return;
          
        const handleScroll = () => {
            if (!!scrollRef.current) {
                isAutoScroll.current = el.scrollHeight - el.scrollTop - el.clientHeight <= 10
            }
            currentScrollHeight.current = el.scrollHeight
        };

        el.addEventListener('scroll', handleScroll);
        return () => el.removeEventListener('scroll', handleScroll);
    }, [])

    const onFinishLoad = () => {
        // setTimeout(() => { 
            if (!!scrollRef?.current && isAutoScroll.current) {
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
            }
        // }, 100)
    }

    // 渲染对应的消息组件
    const renderMessage = (message: Message) => {
        // 移除频繁的日志输出
        // console.log('[MessageList] Rendering message:', message);
        
        if (message.role === 'user') {
            return <UserMessage 
                key={message.id} 
                content={message.content} 
                trace_id={message.trace_id}
                ext={message.ext}
            />;
        }

        if (message.role === 'showcase') {
            return <Showcase />
        }

        if (message.role === 'ai' || message.role === 'tool') {
            const avatar = getAvatar(message.role);
            
            try {
                const response = JSON.parse(message.content);
                // 移除频繁的日志输出
                // console.log('[MessageList] Parsed message content:', response);
                
                // 获取扩展类型
                const workflowExt = response.ext?.find((item: ExtItem) => item.type === 'workflow');
                const nodeExt = response.ext?.find((item: ExtItem) => item.type === 'node');
                const downstreamSubgraphsExt = response.ext?.find((item: ExtItem) => item.type === 'downstream_subgraph_search');
                const nodeInstallGuideExt = response.ext?.find((item: ExtItem) => item.type === 'node_install_guide');
                const paramUpdateExt = response.ext?.find((item: ExtItem) => item.type === 'param_update');
                const workflowUpdateExt = response.ext?.find((item: ExtItem) => item.type === 'workflow_update');
                const debugCheckpointExt = response.ext?.find((item: ExtItem) => item.type === 'debug_checkpoint');
                const workflowUpdateCompleteExt = response.ext?.find((item: ExtItem) => item.type === 'workflow_update_complete');
                
                // 检查是否是工作流成功加载的消息
                const isWorkflowSuccessMessage = response.text === 'The workflow has been successfully loaded to the canvas';

                // 处理工作流更新：实时更新画布 
                if (workflowUpdateExt && workflowUpdateExt.data) {
                    const { workflow_data } = workflowUpdateExt.data;
                    if (typeof window !== 'undefined' && (window as any).app && workflow_data) {
                        // 使用更具体的key，包含workflow_data的hash以检测实际内容变化
                        const contentHash = JSON.stringify(workflow_data).slice(0, 100); // 简单的内容标识
                        const workflowUpdateKey = `workflow_update_${message.id}_${contentHash}`;
                        
                        if (!processedUpdates.current.has(workflowUpdateKey)) {
                            const applyWorkflowWithRetry = async (retryCount = 0) => {
                                try {
                                    const { applyNewWorkflow } = await import('../../utils/graphUtils');
                                    const success = applyNewWorkflow(workflow_data);
                                    
                                    if (success) {
                                        console.log('[MessageList] Successfully applied workflow update');
                                        // 标记该更新已处理（只有成功时才标记）
                                        processedUpdates.current.add(workflowUpdateKey);
                                    } else {
                                        console.warn(`[MessageList] Failed to apply workflow update (attempt ${retryCount + 1})`);
                                        // 重试最多3次
                                        if (retryCount < 2) {
                                            setTimeout(() => {
                                                applyWorkflowWithRetry(retryCount + 1);
                                            }, 1000 * (retryCount + 1)); // 递增延迟：1s, 2s
                                        } else {
                                            console.error('[MessageList] Workflow update failed after 3 attempts');
                                        }
                                    }
                                } catch (error) {
                                    console.error(`[MessageList] Error in workflow update (attempt ${retryCount + 1}):`, error);
                                    // 重试最多3次
                                    if (retryCount < 2) {
                                        setTimeout(() => {
                                            applyWorkflowWithRetry(retryCount + 1);
                                        }, 1000 * (retryCount + 1));
                                    }
                                }
                            };
                            
                            applyWorkflowWithRetry();
                        }
                    }
                }

                
                // 处理参数更新：实时更新画布 
                // "changes": [
                //     {
                //         "node_id": "4",
                //         "parameter": "ckpt_name",
                //         "old_value": "v1-5-pruned-emaonly-fp16.safetensors",
                //         "new_value": "dreamshaperXL_v21TurboDPMSDE.safetensors"
                //     }
                // ]
                if (paramUpdateExt && paramUpdateExt.data) {
                    const { changes } = paramUpdateExt.data;
                    if (typeof window !== 'undefined' && (window as any).app && changes) {
                        // 使用更具体的key，包含changes的hash以检测实际内容变化
                        const contentHash = JSON.stringify(changes).slice(0, 100); // 简单的内容标识
                        const paramUpdateKey = `param_update_${message.id}_${contentHash}`;
                        
                        if (!processedUpdates.current.has(paramUpdateKey)) {
                            const applyParamsWithRetry = async (retryCount = 0) => {
                                try {
                                    const { applyParameterChanges } = await import('../../utils/graphUtils');
                                    // 支持单个change对象或changes数组
                                    const changesList = Array.isArray(changes) ? changes : [changes];
                                    const success = applyParameterChanges(changesList);
                                    
                                    if (success) {
                                        console.log(`[MessageList] Successfully applied ${changesList.length} parameter changes`);
                                        // 标记该更新已处理（只有成功时才标记）
                                        processedUpdates.current.add(paramUpdateKey);
                                    } else {
                                        console.warn(`[MessageList] Failed to apply parameter changes (attempt ${retryCount + 1})`);
                                        // 重试最多3次
                                        if (retryCount < 2) {
                                            setTimeout(() => {
                                                applyParamsWithRetry(retryCount + 1);
                                            }, 1000 * (retryCount + 1)); // 递增延迟：1s, 2s
                                        } else {
                                            console.error('[MessageList] Parameter update failed after 3 attempts');
                                        }
                                    }
                                } catch (error) {
                                    console.error(`[MessageList] Error in parameter update (attempt ${retryCount + 1}):`, error);
                                    // 重试最多3次
                                    if (retryCount < 2) {
                                        setTimeout(() => {
                                            applyParamsWithRetry(retryCount + 1);
                                        }, 1000 * (retryCount + 1));
                                    }
                                }
                            };
                            
                            applyParamsWithRetry();
                        }
                    }
                }

                // 检查是否需要保存当前工作流的UI格式数据
                // 如果ext数据中包含checkpoint_id且消息已完成，保存当前前端的workflow_ui
                if (response.ext && message.finished) {
                    const checkpointExt = response.ext.find((item: ExtItem) => 
                        item.data && item.data.checkpoint_id && 
                        (item.type === 'debug_checkpoint' || item.type === 'workflow_rewrite_complete' || item.type === 'workflow_update_complete')
                    );
                    
                    if (checkpointExt && checkpointExt.data?.checkpoint_id) {
                        const checkpointId = checkpointExt.data.checkpoint_id;
                        const saveWorkflowUIKey = `save_workflow_ui_${message.id}_${checkpointId}`;
                        
                        if (!processedUpdates.current.has(saveWorkflowUIKey)) {
                            const saveWorkflowUIWithRetry = async (retryCount = 0) => {
                                try {
                                    // 获取当前工作流的UI格式数据
                                    if (typeof window !== 'undefined' && (window as any).app) {
                                        const app = (window as any).app;
                                        if (app.graph) {
                                            const workflowPrompt = await app.graphToPrompt();
                                            const workflowUI = workflowPrompt.workflow; // UI format
                                            
                                            if (workflowUI) {
                                                // 调用API更新workflow_ui字段
                                                const response = await fetch('/api/update-workflow-ui', {
                                                    method: 'POST',
                                                    headers: {
                                                        'Content-Type': 'application/json'
                                                    },
                                                    body: JSON.stringify({
                                                        checkpoint_id: checkpointId,
                                                        workflow_data_ui: workflowUI
                                                    })
                                                });
                                                
                                                const result = await response.json();
                                                if (result.success) {
                                                    console.log(`[MessageList] Successfully saved workflow UI for checkpoint ${checkpointId}`);
                                                    processedUpdates.current.add(saveWorkflowUIKey);
                                                } else {
                                                    console.warn(`[MessageList] Failed to save workflow UI for checkpoint ${checkpointId}: ${result.message}`);
                                                    // 重试最多3次
                                                    if (retryCount < 2) {
                                                        setTimeout(() => {
                                                            saveWorkflowUIWithRetry(retryCount + 1);
                                                        }, 1000 * (retryCount + 1));
                                                    } else {
                                                        console.error(`[MessageList] Save workflow UI failed after 3 attempts for checkpoint ${checkpointId}`);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                } catch (error) {
                                    console.error(`[MessageList] Error saving workflow UI (attempt ${retryCount + 1}):`, error);
                                    // 重试最多3次
                                    if (retryCount < 2) {
                                        setTimeout(() => {
                                            saveWorkflowUIWithRetry(retryCount + 1);
                                        }, 1000 * (retryCount + 1));
                                    }
                                }
                            };
                            
                            saveWorkflowUIWithRetry();
                        }
                    }
                }

                // 根据扩展类型添加对应组件
                let ExtComponent = null;
                if (workflowExt) {
                    ExtComponent = (
                        <Suspense fallback={<div>Loading...</div>}>
                            <LazyWorkflowOption
                                content={message.content}
                                name={message.name}
                                avatar={avatar}
                                latestInput={latestInput}
                                installedNodes={installedNodes}
                                onAddMessage={onAddMessage}
                                onFinishLoad={onFinishLoad}
                            />
                        </Suspense>
                    );
                } else if (nodeExt) {
                    ExtComponent = (
                        <Suspense fallback={<div>Loading...</div>}>
                            <LazyNodeSearch
                                content={message.content}
                                name={message.name}
                                avatar={avatar}
                                installedNodes={installedNodes}
                                onFinishLoad={onFinishLoad}
                            />
                        </Suspense>
                    );
                } else if (downstreamSubgraphsExt) {
                    const dsExtComponent = (
                        <Suspense fallback={<div>Loading...</div>}>
                            <LazyDownstreamSubgraphs
                                content={message.content}
                                name={message.name}
                                avatar={avatar}
                                onAddMessage={onAddMessage}
                                onFinishLoad={onFinishLoad}
                            />
                        </Suspense>
                    );
                    
                    // If this is specifically from an intent button click (not regular message parsing)
                    if (message.metadata?.intent === 'downstream_subgraph_search') {
                        // Return the AIMessage with the extComponent
                        return (
                            <AIMessage 
                                key={message.id}
                                content={message.content}
                                name={message.name}
                                avatar={avatar}
                                format={message.format}
                                onOptionClick={onOptionClick}
                                extComponent={dsExtComponent}
                                metadata={message.metadata}
                                finished={message.finished}
                                debugGuide={message.debugGuide}
                            />
                        );
                    }
                    
                    // For normal detection from ext, use the ExtComponent directly
                    ExtComponent = dsExtComponent;
                } else if (nodeInstallGuideExt) {
                    ExtComponent = (
                        <Suspense fallback={<div>Loading...</div>}>
                            <LazyNodeInstallGuide
                                content={message.content}
                                onLoadSubgraph={() => {
                                    if (message.metadata?.pendingSubgraph) {
                                        const selectedNode = Object.values(app.canvas.selected_nodes)[0] as any;
                                        if (selectedNode) {
                                            // 直接调用 DownstreamSubgraphs 中的 loadSubgraphToCanvas
                                            const node = message.metadata.pendingSubgraph;
                                            const nodes = node.json.nodes;
                                            const links = node.json.links;
                                            
                                            const entryNode = nodes.find((n: any) => n.id === 0);
                                            const entryNodeId = entryNode?.id;

                                            const nodeMap: NodeMap = {};
                                            if (entryNodeId) {
                                                nodeMap[entryNodeId] = selectedNode;
                                            }
                                            
                                            // 创建其他所有节点
                                            app.canvas.emitBeforeChange();
                                            try {
                                                for (const node of nodes as NodeWithPosition[]) {
                                                    if (node.id !== entryNodeId) {
                                                        const posEntryOld = entryNode?.pos || [0, 0];
                                                        const posEntryNew = selectedNode._pos || [0, 0];
                                                        const nodePosNew = [
                                                            node.pos[0] + posEntryNew[0] - posEntryOld[0], 
                                                            node.pos[1] + posEntryNew[1] - posEntryOld[1]
                                                        ];
                                                        nodeMap[node.id] = addNodeOnGraph(node.type, {pos: nodePosNew});
                                                    }
                                                }
                                            } finally {
                                                app.canvas.emitAfterChange();
                                            }

                                            // 处理所有连接
                                            for (const link of links) {
                                                const origin_node = nodeMap[link['origin_id']];
                                                const target_node = nodeMap[link['target_id']];
                                                
                                                if (origin_node && target_node) {
                                                    origin_node.connect(
                                                        link['origin_slot'], 
                                                        target_node, 
                                                        link['target_slot']
                                                    );
                                                }
                                            }
                                        } else {
                                            alert("Please select a upstream node first before adding a subgraph.");
                                        }
                                    } else if (message.metadata?.pendingWorkflow) {
                                        const workflow = message.metadata.pendingWorkflow;
                                        const optimizedParams = message.metadata.optimizedParams;
                                       
                                        // TODO: 支持不同格式的工作流
                                        if(workflow.nodes) {
                                            app.loadGraphData(workflow);
                                        } else {
                                            app.loadApiJson(workflow);
                                            // 获取所有节点，并且优化排布
                                            const node_ids = Object.keys(workflow);
                                            
                                            // 获取第一个节点作为基准位置
                                            const firstNodeId = Object.keys(app.graph._nodes_by_id)[0];
                                            const firstNode = app.graph._nodes_by_id[firstNodeId];
                                            const base_x = firstNode ? firstNode.pos[0] : 0;
                                            const base_y = firstNode ? firstNode.pos[1] : 0;
                                            
                                            // 布局参数
                                            const base_size_x = 250;
                                            const base_size_y = 60;
                                            const param_y = 20;
                                            const align = 60;
                                            const align_y = 50;
                                            const max_size_y = 1000;
                                            
                                            let last_start_x = base_x;
                                            let last_start_y = base_y;
                                            let tool_size_y = 0;
                                            
                                            for(const node_id of node_ids) {
                                                const node = app.graph._nodes_by_id[node_id];
                                                if(node) {
                                                    // 检查是否需要换列
                                                    if (tool_size_y > max_size_y) {
                                                        last_start_x += base_size_x + align;
                                                        tool_size_y = 0;
                                                        last_start_y = base_y;
                                                    }

                                                    // 根据参数计算节点的高度
                                                    const inputCount = node.inputs ? node.inputs.length : 0;
                                                    const outputCount = node.outputs ? node.outputs.length : 0;
                                                    const widgetCount = node.widgets ? node.widgets.length : 0;
                                                    const param_count = Math.max(inputCount, outputCount) + widgetCount;
                                                    
                                                    const size_y = param_y * param_count + base_size_y;
                                                    
                                                    // 设置节点大小和位置
                                                    node.size[0] = base_size_x;
                                                    node.size[1] = size_y;
                                                    node.pos[0] = last_start_x;
                                                    node.pos[1] = last_start_y;

                                                    tool_size_y += size_y + align_y;
                                                    last_start_y += size_y + align_y;
                                                }
                                            }
                                        }
                                        
                                        // 应用优化参数
                                        for (const [nodeId, nodeName, paramIndex, paramName, value] of optimizedParams) {
                                            const widgets = app.graph._nodes_by_id[nodeId].widgets;
                                            for (const widget of widgets) {
                                                if (widget.name === paramName) {
                                                    widget.value = value;
                                                }
                                            }
                                        }
                                        app.graph.setDirtyCanvas(false, true);
                                        // Add success message
                                        const successMessage = {
                                            id: generateUUID(),
                                            role: 'tool',
                                            content: JSON.stringify({
                                                text: 'The workflow has been successfully loaded to the canvas',
                                                ext: []
                                            }),
                                            format: 'markdown',
                                            name: 'Assistant'
                                        };
                                        onAddMessage?.(successMessage);
                                    }
                                }}
                                onFinishLoad={onFinishLoad}
                            />
                        </Suspense>
                    );
                } else if (isWorkflowSuccessMessage || message.format === 'debug_guide') {
                    // 使用DebugGuide组件来处理工作流成功加载的消息或debug_guide格式的消息
                    ExtComponent = (
                        <Suspense fallback={<div>Loading...</div>}>
                            <LazyDebugGuide
                                content={message.content}
                                name={message.name}
                                avatar={avatar}
                                onAddMessage={onAddMessage}
                                onUpdateMessage={onUpdateMessage}
                                onFinishLoad={onFinishLoad}
                                messageId={message.id}
                            />
                        </Suspense>
                    );
                } else if (debugCheckpointExt) {
                    // 使用DebugResult组件来处理有debug checkpoint的消息
                    // 只有在finished=true时才使用卡片形式的DebugResult，否则不设置ExtComponent，让它走普通AIMessage逻辑
                    if (message.finished) {
                        ExtComponent = (
                            <Suspense fallback={<div>Loading...</div>}>
                                <LazyDebugResult
                                    content={message.content}
                                    name={message.name}
                                    avatar={avatar}
                                    format={message.format}
                                    onFinishLoad={onFinishLoad}
                                />
                            </Suspense>
                        );
                    }
                } else if (workflowUpdateExt || paramUpdateExt) {
                    // 处理工作流更新或参数更新结果消息
                    // 只有在finished=true时才使用卡片形式的DebugResult，否则不设置ExtComponent，让它走普通AIMessage逻辑
                    if (message.finished) {
                        ExtComponent = (
                            <Suspense fallback={<div>Loading...</div>}>
                                <LazyDebugResult
                                    content={message.content}
                                    name={message.name}
                                    avatar={avatar}
                                    format={message.format}
                                    onFinishLoad={onFinishLoad}
                                />
                            </Suspense>
                        );
                    }
                }

                // 如果是工作流成功消息或debug_guide格式，直接返回DebugGuide组件
                if ((isWorkflowSuccessMessage || message.format === 'debug_guide') && ExtComponent) {
                    return ExtComponent;
                }

                // 如果有debug checkpoint且已完成，直接返回DebugResult组件
                if (debugCheckpointExt && message.finished && ExtComponent) {
                    return ExtComponent;
                }

                // 如果有workflow_update或param_update且已完成，直接返回DebugResult组件
                if ((workflowUpdateExt || paramUpdateExt) && message.finished && ExtComponent) {
                    return ExtComponent;
                }

                // 如果有response.text，使用AIMessage渲染
                if (response.text || ExtComponent) {
                    return (
                        <AIMessage 
                            key={message.id}
                            content={message.content}
                            name={message.name}
                            avatar={avatar}
                            format={message.format}
                            onOptionClick={onOptionClick}
                            extComponent={ExtComponent}
                            metadata={message.metadata}
                            finished={message.finished}
                            debugGuide={message.debugGuide}
                        />
                    );
                }

                // 如果没有response.text但有扩展组件，直接返回扩展组件
                if (ExtComponent) {
                    return ExtComponent;
                }

                // 默认返回AIMessage
                return (
                    <AIMessage 
                        key={message.id}
                        content={message.content}
                        name={message.name}
                        avatar={avatar}
                        format={message.format}
                        onOptionClick={onOptionClick}
                        metadata={message.metadata}
                        finished={message.finished}
                        debugGuide={message.debugGuide}
                    />
                );
            } catch (error) {
                // console.error('[MessageList] Error parsing message content:', error);
                // 如果解析JSON失败,使用AIMessage
                // console.error('解析JSON失败', message.content);
                return (
                    <AIMessage 
                        key={message.id}
                        content={message.content}
                        name={message.name}
                        avatar={avatar}
                        format={message.format}
                        onOptionClick={onOptionClick}
                        metadata={message.metadata}
                        finished={message.finished}
                        debugGuide={message.debugGuide}
                    />
                );
            }
        }

        return null;
    }

    const renderLoadMore = (message: LoadMoreButtonProps) => {
        const isNotUsed = message?.buttonStatus === LoadMoreStatus.NOT_USED
        return <div 
            key={message.id}
            className='flex justify-center items-center'
        >
            {
                isNotUsed ? <button 
                    className='w-full h-[24px] text-gray-700 text-xs bg-transparent hover:!bg-gray-100 px-2 py-1 rounded-md'
                    onClick={handleLoadMore}
                >
                    Load more
                </button> : <div className='w-full h-[24px] bg-transparent' />
            }
        </div>
    }

    function isLoadMoreButtonProps(item: any): item is LoadMoreButtonProps {
        return item && typeof item === 'object' && item.buttonType === 'loadmore';
    }

    const handleLoadMore = () => {
        isLoadHistory.current = true;
        setCurrentIndex(index => index + 1);
    }

    useEffect(() => {
        // 先处理消息，关联checkpoint信息到用户消息
        const processedMessages = processMessagesWithCheckpoints(messages);
        
        let list: FinallyMessageProps[] = []
        if (lastMessagesCount.current > 0 && lastMessagesCount.current < processedMessages.length) {
            list = processedMessages.slice(lastMessagesCount.current)
            if (processedMessages[lastMessagesCount.current].role === 'user') {
                list.unshift({  
                    id: `${processedMessages[lastMessagesCount.current].id}_loadmore`,
                    buttonType: 'loadmore',
                    buttonStatus: LoadMoreStatus.USED
                })
            }
            setCurrentMessages(pre => [...pre, ...list]);
        } else {
            let count = 0;
            let endIndex = processedMessages?.length
            for (let i = processedMessages?.length - 1; i >= 0; i--) {
                if (processedMessages[i].role === 'ai' || i === 0) {
                    if (count > DEFAULT_COUNT + currentIndex) {
                        list.unshift({
                            id: `${processedMessages[i].id}_loadmore`,
                            buttonType: 'loadmore',
                            buttonStatus: LoadMoreStatus.NOT_USED
                        })
                        break;
                    } else {
                        count++;    
                        if (list?.length > 0) {
                            list.unshift({
                                id: `${processedMessages[i].id}_loadmore`,
                                buttonType: 'loadmore',
                                buttonStatus: LoadMoreStatus.USED
                            })
                        }
                        list = [
                            ...processedMessages?.slice(Math.min(endIndex, i === 0 ? i : i + 1), endIndex + 1), 
                            ...list
                        ];
                        endIndex = i;
                    }
                }
            }
            setCurrentMessages(list)
        }
        lastMessagesCount.current = processedMessages.length
    }, [messages, currentIndex])

    useLayoutEffect(() => {
        if (!!scrollRef?.current) {
            if (isLoadHistory.current) {
                // 加载历史数据需要修改scrolltop保证当前视图不变
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight - currentScrollHeight.current
                isLoadHistory.current = false
            } else {
                if (isAutoScroll.current) {
                    scrollRef.current.scrollTop = scrollRef.current.scrollHeight
                }
            }
            currentScrollHeight.current = scrollRef.current.scrollHeight
        }
    }, [currentMessages])

    return (
        <div 
            className='flex-1 flex-col overflow-y-auto p-4 h-0'
            ref={scrollRef} 
            style={{
                display: isActive ? 'block' : 'none',
            }}
        >
            {
                currentMessages?.map((message) => !!message && (isLoadMoreButtonProps(message) ? renderLoadMore(message as LoadMoreButtonProps) : renderMessage(message as Message)))
            }
            {loading && <LoadingMessage />}
        </div>
    );
} 