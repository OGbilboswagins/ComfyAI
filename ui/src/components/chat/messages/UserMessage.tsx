
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { BaseMessage } from './BaseMessage';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import RestoreCheckpoint from '../../ui/RestoreCheckpoint';

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
    let images: any[] = [];
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
        
        const hasImages = ext.some((item) => item.type === 'img');
        if (hasImages) {
            ext.filter((item) => item.type === 'img').forEach((item) => images = images.concat(item.data));
        }
        // If we have workflow/param updates but no checkpoint, we could show a message about it
        // But for now, we only show restore button if we have a checkpoint
    }

    return (
        <BaseMessage name="User" isUser={true}>
            <div className="w-full rounded-lg border border-gray-700 p-4 text-gray-700 text-sm break-words">
                {
                    images.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                            {images.map((image) => (
                                <img src={image.url} alt={image.name} className="w-16 h-16 object-cover" />
                            ))}
                        </div>
                    )
                }
                <p className="whitespace-pre-wrap leading-snug">{content}</p>
                
                {/* Bottom right icons container */}
                <div className="flex justify-end">
                    <div className="flex items-center space-x-1 -mb-2">
                        {/* Restore checkpoint icon */}
                        {checkpointId && (
                            <RestoreCheckpoint 
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
            </div>
        </BaseMessage>
    );
} 