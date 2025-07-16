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
    const [streamingText, setStreamingText] = useState('');
    const [showStreamingMessage, setShowStreamingMessage] = useState(false);
    
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
            await handleQueueError();
        } finally {
            setIsDebugging(false);
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

    const handleQueuePrompt = async () => {
        const result = await queuePrompt([]);
        console.log('Queue result:', result);
    };

    return (
        <div className="w-full space-y-4">
            {/* Original message */}
            <BaseMessage name={name}>
                <div className="space-y-3">
                    <p className="text-gray-700 text-sm">
                        {response.text}
                    </p>
                    
                    <div className="flex gap-2">
                        <button
                            onClick={handleQueuePrompt}
                            className="px-4 py-2 bg-green-500 text-white text-sm rounded-md hover:bg-green-600 transition-colors"
                        >
                            Queue Prompt
                        </button>
                        
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
