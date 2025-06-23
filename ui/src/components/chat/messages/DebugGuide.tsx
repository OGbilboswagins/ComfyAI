import React, { useState } from 'react';
import { BaseMessage } from './BaseMessage';
import { generateUUID } from '../../../utils/uuid';
import { queuePrompt } from '../../../utils/queuePrompt';
import { app } from '../../../utils/comfyapp';
import { WorkflowChatAPI } from '../../../apis/workflowChatApi';

interface DebugGuideProps {
    content: string;
    name?: string;
    avatar: string;
    onAddMessage?: (message: any) => void;
}

export function DebugGuide({ content, name = 'Assistant', avatar, onAddMessage }: DebugGuideProps) {
    const [isDebugging, setIsDebugging] = useState(false);
    
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
        
        try {
            // Get current workflow
            const prompt = await app.graphToPrompt();
            console.log('Current workflow:', prompt);
            
            // Queue the prompt to check for errors
            const queueResponse = await queuePrompt([]);
            console.log('Queue response:', queueResponse);
            
            // Check if we received an error response (even if the request "succeeded")
            if (queueResponse.error || queueResponse.node_errors) {
                // Handle structured error response
                await handleQueueError(queueResponse);
            } else {
                // If we get here without errors, the workflow is working fine
                const successMessage = {
                    id: generateUUID(),
                    role: 'ai',
                    content: JSON.stringify({
                        text: 'Great! I tested your workflow and it appears to be working correctly. No errors were found during the validation process.',
                        ext: []
                    }),
                    format: 'markdown',
                    name: 'Assistant'
                };
                onAddMessage?.(successMessage);
            }
        } finally {
            setIsDebugging(false);
        }
    };

    const handleQueueError = async (errorData: any) => {
        try {
            // Get current workflow for context
            const prompt = await app.graphToPrompt();
            
            let accumulatedText = '';
            let finalExt: any = null;

            // Use the streaming debug agent API
            for await (const result of WorkflowChatAPI.streamDebugAgent(errorData, prompt)) {
                if (result.text) {
                    accumulatedText = result.text;
                    if (result.ext) {
                        finalExt = result.ext;
                    }
                    // Don't add message here - wait for completion
                }
            }

            // Only add the final complete message after streaming is done
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
        <BaseMessage name={name}>
            <div className="space-y-3">
                <div className="text-sm text-gray-600 mb-3">
                    {response.text}
                </div>
                
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex-1">
                        <p className="text-sm text-blue-800">
                            Would you like me to help debug this workflow?
                        </p>
                    </div>
                    <button
                        onClick={handleDebugClick}
                        disabled={isDebugging}
                        className={`px-4 py-2 rounded-md transition-colors text-sm font-medium ${
                            isDebugging 
                                ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                                : 'bg-blue-500 hover:bg-blue-600 text-white'
                        }`}
                    >
                        {isDebugging ? 'Debugging...' : 'Debug'}
                    </button>
                </div>
            </div>
        </BaseMessage>
    );
}
