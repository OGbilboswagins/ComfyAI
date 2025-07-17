import React, { useState } from 'react';
import { BaseMessage } from './BaseMessage';
import { generateUUID } from '../../../utils/uuid';
import { queuePrompt } from '../../../utils/queuePrompt';
import { app } from '../../../utils/comfyapp';
import { WorkflowChatAPI } from '../../../apis/workflowChatApi';

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

interface DebugGuideProps {
    content: string;
    name?: string;
    avatar: string;
    onAddMessage?: (message: any) => void;
}

export function DebugGuide({ content, name = 'Assistant', avatar, onAddMessage }: DebugGuideProps) {
    const [isDebugging, setIsDebugging] = useState(false);
    const [streamingText, setStreamingText] = useState('');
    const [showStreamingMessage, setShowStreamingMessage] = useState(false);
    const [checkpointId, setCheckpointId] = useState<number | null>(null);
    
    // Parse the message content
    let response;
    try {
        response = JSON.parse(content);
    } catch (error) {
        console.error('Failed to parse message content:', error);
        return null;
    }

    const handleDebugClick = async () => {
        if (isDebugging) return;
        
        setIsDebugging(true);
        setShowStreamingMessage(true);
        setStreamingText('🔍 Starting workflow analysis...\n');
        
        try {
            // Save checkpoint before debugging
            await saveCheckpointBeforeDebug();
            
            await handleQueueError();
        } finally {
            setIsDebugging(false);
        }
    };

    const saveCheckpointBeforeDebug = async () => {
        try {
            const prompt = await app.graphToPrompt();
            const sessionId = localStorage.getItem("sessionId") || '';
            
            if (sessionId && prompt) {
                const checkpointData = await WorkflowChatAPI.saveWorkflowCheckpoint(
                    sessionId,
                    prompt.output, // API format
                    prompt.workflow, // UI format
                    'debug_start'
                );
                
                setCheckpointId(checkpointData.version_id);
                console.log(`Saved debug start checkpoint: ${checkpointData.version_id}`);
            }
        } catch (error) {
            console.error('Failed to save checkpoint before debug:', error);
            // Continue with debug even if checkpoint save fails
        }
    };

    const handleQueueError = async () => {
        try {
            // Get current workflow for context
            const prompt = await app.graphToPrompt();
            
            let accumulatedText = '';
            let finalExt: any = null;

            // Use the streaming debug agent API
            for await (const result of WorkflowChatAPI.streamDebugAgent(prompt)) {
                if (result.text) {
                    accumulatedText = result.text;
                    setStreamingText(accumulatedText); // Update streaming text in real-time
                    if (result.ext) {
                        finalExt = result.ext;
                    }
                }
            }

            // Hide streaming message and add final complete message
            setShowStreamingMessage(false);
            
            if (accumulatedText) {
                const debugMessage = {
                    id: generateUUID(),
                    role: 'ai' as const,
                    content: JSON.stringify({
                        text: accumulatedText,
                        ext: finalExt || []
                    }),
                    format: 'markdown',
                    name: 'Assistant'
                };
                onAddMessage?.(debugMessage);
            }

        } catch (error: unknown) {
            console.error('Error calling debug agent:', error);
            setShowStreamingMessage(false);
            const errorObj = error as any;
            const errorMessage = {
                id: generateUUID(),
                role: 'ai' as const,
                content: JSON.stringify({
                    text: `I encountered an error while analyzing your workflow: ${errorObj.message || 'Unknown error'}`,
                    ext: []
                }),
                format: 'markdown',
                name: 'Assistant'
            };
            onAddMessage?.(errorMessage);
        }
    };

    return (
        <div className="w-full space-y-4">
            {/* Original message */}
            <BaseMessage name={name}>
                <div className="space-y-3">
                    <div className="flex justify-between items-start">
                        <p className="text-gray-700 text-sm flex-1">
                            {response.text}
                        </p>
                        
                        {/* Restore checkpoint icon */}
                        {checkpointId && (
                            <div className="ml-2 flex-shrink-0">
                                <RestoreCheckpointIcon 
                                    checkpointId={checkpointId} 
                                    onRestore={() => {
                                        console.log('Workflow restored from checkpoint');
                                    }}
                                />
                            </div>
                        )}
                    </div>
                    
                    <div className="flex gap-2">
                        <button
                            onClick={handleDebugClick}
                            disabled={isDebugging}
                            className={`px-4 py-2 text-white text-sm rounded-md transition-colors ${
                                isDebugging 
                                    ? 'bg-gray-400 cursor-not-allowed' 
                                    : 'bg-blue-500 hover:bg-blue-600'
                            }`}
                        >
                            {isDebugging ? 'Analyzing...' : 'Debug Errors'}
                        </button>
                    </div>
                </div>
            </BaseMessage>

            {/* Streaming message */}
            {showStreamingMessage && (
                <BaseMessage name="Assistant">
                    <div className="space-y-3">
                        <div className="prose prose-sm max-w-none">
                            <pre className="whitespace-pre-wrap text-gray-700 text-sm leading-relaxed">
                                {streamingText}
                            </pre>
                        </div>
                        {isDebugging && (
                            <div className="flex items-center gap-2 text-blue-500 text-sm">
                                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                                Analyzing workflow...
                            </div>
                        )}
                    </div>
                </BaseMessage>
            )}
        </div>
    );
}
