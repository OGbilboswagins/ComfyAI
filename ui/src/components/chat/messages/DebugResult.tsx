import React, { useState } from 'react';
import { BaseMessage } from './BaseMessage';
import { WorkflowChatAPI } from '../../../apis/workflowChatApi';
import { app } from '../../../utils/comfyapp';

// Restore checkpoint icon component
const RestoreCheckpointIcon = ({ checkpointId, onRestore }: { checkpointId: number; onRestore: () => void }) => {
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
            title={`Restore checkpoint ${checkpointId}`}
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
}

export function DebugResult({ content, name = 'Assistant', avatar, format = 'markdown' }: DebugResultProps) {
    // Parse the message content
    let response;
    let checkpointId: number | null = null;
    
    try {
        response = JSON.parse(content);
        
        // Look for debug_checkpoint in ext data
        if (response.ext) {
            const checkpointExt = response.ext.find((item: any) => item.type === 'debug_checkpoint');
            if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
                checkpointId = checkpointExt.data.checkpoint_id;
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

    return (
        <BaseMessage name={name}>
            <div className="space-y-3">
                <div className="flex justify-between items-start">
                    <div className="flex-1 prose prose-sm max-w-none">
                        {format === 'markdown' ? (
                            <div 
                                className="text-gray-700 text-sm leading-relaxed"
                                dangerouslySetInnerHTML={{ __html: formatContent(response.text || '') }}
                            />
                        ) : (
                            <pre className="whitespace-pre-wrap text-gray-700 text-sm leading-relaxed">
                                {response.text || ''}
                            </pre>
                        )}
                    </div>
                    
                    {/* Restore checkpoint icon */}
                    {checkpointId && (
                        <div className="ml-2 flex-shrink-0">
                            <RestoreCheckpointIcon 
                                checkpointId={checkpointId} 
                                onRestore={() => {
                                    console.log('Workflow restored from debug completion checkpoint');
                                }}
                            />
                        </div>
                    )}
                </div>
            </div>
        </BaseMessage>
    );
} 