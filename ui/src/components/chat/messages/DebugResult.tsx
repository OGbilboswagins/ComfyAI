import React, { useEffect, useState } from 'react';
import { BaseMessage } from './BaseMessage';
import { WorkflowChatAPI } from '../../../apis/workflowChatApi';
import { app } from '../../../utils/comfyapp';

// Restore checkpoint icon component
const RestoreCheckpointIcon = ({ checkpointId, onRestore, title }: { checkpointId: number; onRestore: () => void; title?: string }) => {
    const [isRestoring, setIsRestoring] = useState(false);

    const handleRestore = async () => {
        if (isRestoring) return;
        
        setIsRestoring(true);
        try {
            const checkpointData = await WorkflowChatAPI.restoreWorkflowCheckpoint(checkpointId);
            
            // Use UI format if available, otherwise use API format
            const workflowToLoad = checkpointData.workflow_data_ui || checkpointData.workflow_data;
            
            if (workflowToLoad) {
                // Load workflow to canvas
                if (checkpointData.workflow_data_ui) {
                    // UI format - use loadGraphData
                    app.loadGraphData(workflowToLoad);
                } else {
                    // API format - use loadApiJson
                    app.loadApiJson(workflowToLoad);
                }
                
                console.log(`Restored workflow checkpoint ${checkpointId}`);
                onRestore();
            } else {
                console.error('No workflow data found in checkpoint');
                alert('No workflow data found in checkpoint.');
            }
        } catch (error) {
            console.error('Failed to restore checkpoint:', error);
            alert('Failed to restore workflow checkpoint. Please try again.');
        } finally {
            setIsRestoring(false);
        }
    };

    return (
        <button
            onClick={handleRestore}
            disabled={isRestoring}
            className={`p-1 rounded transition-colors ${
                isRestoring 
                    ? 'text-gray-400 cursor-not-allowed' 
                    : 'text-gray-500 hover:text-blue-600 hover:bg-blue-50'
            }`}
            title={title || `Restore checkpoint ${checkpointId}`}
        >
            <svg 
                width="16" 
                height="16" 
                viewBox="0 0 16 16" 
                fill="currentColor"
                className={isRestoring ? 'animate-spin' : ''}
            >
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V2.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 6.658A.25.25 0 0 1 8 6.466z"/>
            </svg>
        </button>
    );
};

interface DebugResultProps {
    content: string;
    name?: string;
    avatar: string;
    format?: string;
    onFinishLoad?: () => void;
}

export function DebugResult({ content, name = 'Assistant', avatar, format = 'markdown', onFinishLoad }: DebugResultProps) {
    // Parse the message content
    useEffect(() => {
        onFinishLoad?.()
    }, [])
    
    let response;
    let checkpointId: number | null = null;
    let isWorkflowUpdate = false;
    
    try {
        response = JSON.parse(content);
        
        // Check for different types of checkpoints
        if (response.ext) {
            // Look for workflow_rewrite_checkpoint (from workflow updates - 修改前的版本)
            let checkpointExt = response.ext.find((item: any) => 
                item.type === 'workflow_rewrite_checkpoint' || 
                (item.type === 'debug_checkpoint' && item.data?.checkpoint_type === 'workflow_rewrite_start')
            );
            
            if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
                checkpointId = checkpointExt.data.checkpoint_id;
                isWorkflowUpdate = true;
            } else {
                // Look for workflow_rewrite_complete (from workflow updates - 修改后的版本)
                checkpointExt = response.ext.find((item: any) => 
                    item.type === 'workflow_rewrite_complete'
                );
                
                if (checkpointExt && checkpointExt.data && checkpointExt.data.version_id) {
                    checkpointId = checkpointExt.data.version_id;
                    isWorkflowUpdate = true;
                } else {
                    // Look for debug_checkpoint (from debug operations)
                    checkpointExt = response.ext.find((item: any) => item.type === 'debug_checkpoint');
                    if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
                        checkpointId = checkpointExt.data.checkpoint_id;
                        isWorkflowUpdate = false;
                    }
                }
            }
            
            // Check if this is a workflow update message
            const workflowUpdateExt = response.ext.find((item: any) => item.type === 'workflow_update');
            if (workflowUpdateExt) {
                isWorkflowUpdate = true;
            }
        }
    } catch (error) {
        console.error('Failed to parse DebugResult content:', error);
        return null;
    }

    const formatContent = (text: string) => {
        if (format === 'markdown') {
            // Simple markdown rendering for basic formatting
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
                .replace(/\n/g, '<br/>');
        }
        return text;
    };

    // Choose styling based on message type
    const containerClass = isWorkflowUpdate 
        ? 'bg-green-50 border border-green-200 p-4 rounded-lg'
        : 'bg-gray-100 p-4 rounded-lg';
    
    const textClass = isWorkflowUpdate 
        ? 'text-green-700 text-sm leading-relaxed'
        : 'text-gray-700 text-sm leading-relaxed';

    const title = isWorkflowUpdate ? (
        <div className="flex items-center mb-2">
            <svg 
                className="w-5 h-5 text-green-600 mr-2" 
                fill="currentColor" 
                viewBox="0 0 20 20"
            >
                <path 
                    fillRule="evenodd" 
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                    clipRule="evenodd" 
                />
            </svg>
            <h4 className="text-green-800 font-medium">Workflow Updated Successfully</h4>
        </div>
    ) : null;

    const helpText = isWorkflowUpdate ? (
        <div className="mt-3 text-xs text-green-600">
            💡 If you're not satisfied with the changes, click the restore button to revert to the previous version.
        </div>
    ) : null;

    return (
        <BaseMessage name={name}>
            <div className={containerClass}>
                <div className="flex justify-between items-start">
                    <div className="flex-1 prose prose-sm max-w-none">
                        {title}
                        
                        {format === 'markdown' ? (
                            <div 
                                className={textClass}
                                dangerouslySetInnerHTML={{ __html: formatContent(response.text || '') }}
                            />
                        ) : (
                            <pre className={`whitespace-pre-wrap ${textClass}`}>
                                {response.text || ''}
                            </pre>
                        )}
                        
                        {helpText}
                    </div>
                    
                    {/* Restore checkpoint icon */}
                    {checkpointId && (
                        <div className="ml-2 flex-shrink-0">
                            <RestoreCheckpointIcon 
                                checkpointId={checkpointId} 
                                onRestore={() => {
                                    console.log(`Workflow restored from ${isWorkflowUpdate ? 'workflow update' : 'debug'} checkpoint`);
                                }}
                                title={isWorkflowUpdate ? `Restore to this version (Version ${checkpointId})` : `Restore checkpoint ${checkpointId}`}
                            />
                        </div>
                    )}
                </div>
            </div>
        </BaseMessage>
    );
} 