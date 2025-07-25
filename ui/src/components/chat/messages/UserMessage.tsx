
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { BaseMessage } from './BaseMessage';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
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
                
                console.log(`Restored workflow checkpoint ${checkpointId} from user message`);
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
            title={title || `Restore to previous version (Checkpoint ${checkpointId})`}
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

interface ExtItem {
    type: string;
    data?: any;
}

interface UserMessageProps {
    content: string;
    trace_id?: string;
    ext?: ExtItem[];
}

export function UserMessage({ content, trace_id, ext }: UserMessageProps) {
    const [showTooltip, setShowTooltip] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleCopyTraceId = async () => {
        if (trace_id) {
            await navigator.clipboard.writeText(trace_id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Check if there's a checkpoint in ext data for workflow_update or param_update
    let checkpointId: number | null = null;
    if (ext) {        
        // Look for workflow_rewrite_checkpoint or debug_checkpoint related to workflow updates
        const checkpointExt = ext.find((item) => 
            item.type === 'workflow_rewrite_checkpoint' || 
            (item.type === 'debug_checkpoint' && item.data?.checkpoint_type === 'workflow_rewrite_start')
        );
        
        if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
            checkpointId = checkpointExt.data.checkpoint_id;
        }
        
        // Also check if there's workflow_update or param_update ext (user might want checkpoint for these)
        const hasWorkflowUpdate = ext.some((item) => 
            item.type === 'workflow_update' || item.type === 'param_update'
        );
        
        // If we have workflow/param updates but no checkpoint, we could show a message about it
        // But for now, we only show restore button if we have a checkpoint
    }

    return (
        <BaseMessage name="User" isUser={true}>
            <div className="w-full rounded-lg border border-gray-700 p-4 text-gray-700 text-sm break-words relative">
                <p className="whitespace-pre-wrap leading-snug">{content}</p>
                
                {/* Bottom right icons container */}
                <div className="absolute bottom-1 right-1.5 flex items-center space-x-1">
                    {/* Restore checkpoint icon */}
                    {checkpointId && (
                        <RestoreCheckpointIcon 
                            checkpointId={checkpointId} 
                            onRestore={() => {
                                console.log('Workflow restored from user message checkpoint');
                            }}
                            title={`Restore to version before this request (Checkpoint ${checkpointId})`}
                        />
                    )}
                    
                    {/* Trace ID icon */}
                    {trace_id && (
                        <div 
                            className="cursor-pointer opacity-40 hover:opacity-100 transition-opacity"
                            onMouseEnter={() => setShowTooltip(true)}
                            onMouseLeave={() => setShowTooltip(false)}
                            onClick={handleCopyTraceId}
                        >
                            <InformationCircleIcon className="h-3.5 w-3.5 text-gray-500 hover:!text-gray-700" />
                            
                            {/* Tooltip */}
                            {showTooltip && (
                                <div className="absolute right-0 -top-6 bg-gray-700 text-white text-[10px] py-0.5 px-1.5 rounded shadow-sm whitespace-nowrap">
                                    {copied ? 'Copied!' : `Copy trace ID`}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </BaseMessage>
    );
} 