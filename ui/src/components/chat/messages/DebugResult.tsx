import { useEffect, useMemo, useState } from 'react';
import { BaseMessage } from './BaseMessage';
import RestoreCheckpoint from '../../ui/RestoreCheckpoint';
import DebugCollapsibleCard from '../../ui/DebugCollapsibleCard';

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
    
    const [responseData, setResponseData] = useState<any>(null);
    const [checkpointId, setCheckpointId] = useState<number | null>(null);
    const [isWorkflowUpdate, setIsWorkflowUpdate] = useState<boolean>(false);
    
    useEffect(() => {
        try {
            const response = JSON.parse(content);
            setResponseData(response);
            // Check for different types of checkpoints
            if (response.ext) {
                // Look for workflow_rewrite_checkpoint (from workflow updates - 修改前的版本)
                let checkpointExt = response.ext.find((item: any) => 
                    item.type === 'workflow_rewrite_checkpoint' || 
                    (item.type === 'debug_checkpoint' && item.data?.checkpoint_type === 'workflow_rewrite_start')
                );
                
                if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
                    setCheckpointId(checkpointExt.data.checkpoint_id);
                    setIsWorkflowUpdate(true);
                } else {
                    // Look for workflow_rewrite_complete (from workflow updates - 修改后的版本)
                    checkpointExt = response.ext.find((item: any) => 
                        item.type === 'workflow_rewrite_complete'
                    );
                    
                    if (checkpointExt && checkpointExt.data && checkpointExt.data.version_id) {
                        setCheckpointId(checkpointExt.data.version_id);
                        setIsWorkflowUpdate(true);
                    } else {
                        // Look for debug_checkpoint (from debug operations)
                        checkpointExt = response.ext.find((item: any) => item.type === 'debug_checkpoint');
                        if (checkpointExt && checkpointExt.data && checkpointExt.data.checkpoint_id) {
                            setCheckpointId(checkpointExt.data.checkpoint_id);
                            setIsWorkflowUpdate(false);
                        }
                    }
                }
                
                // Check if this is a workflow update message
                const workflowUpdateExt = response.ext.find((item: any) => item.type === 'workflow_update');
                if (workflowUpdateExt) {
                    setIsWorkflowUpdate(true);
                }
            }
        } catch (error) {
            console.error('Failed to parse DebugResult content:', error);
        }
    }, [content])
    

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
    const containerClass = useMemo(() => {
        return isWorkflowUpdate 
        ? 'bg-green-50 border border-green-200'
        : 'bg-gray-100';
    }, [isWorkflowUpdate])

    const textClass = useMemo(() => {
        return isWorkflowUpdate 
        ? 'text-green-700 text-sm leading-relaxed'
        : 'text-gray-700 text-sm leading-relaxed';
    }, [isWorkflowUpdate])

    const title = useMemo(() => {
        return isWorkflowUpdate ? (
            <div className="flex items-center">
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
    }, [isWorkflowUpdate])

    const helpText = useMemo(() => {
        return isWorkflowUpdate ? (
            <div className="mt-3 text-xs text-green-600">
                💡 If you're not satisfied with the changes, click the restore button to revert to the previous version.
            </div>
        ) : null;
    }, [isWorkflowUpdate])

    console.log('responseData-', responseData)
    if (!responseData) return null;
    
    return (
        <BaseMessage name={name}>
            <div className="bg-gray-100 p-4 rounded-lg">
                <DebugCollapsibleCard 
                    title={title} 
                    isWorkflowUpdate={isWorkflowUpdate} 
                    className={containerClass}
                >
                    <div className="flex-1 prose prose-sm max-w-none">
                        {/* {title} */}
                        
                        {format === 'markdown' ? (
                            <div 
                                className={textClass}
                                dangerouslySetInnerHTML={{ __html: formatContent(responseData.text || '') }}
                            />
                        ) : (
                            <pre className={`whitespace-pre-wrap ${textClass}`}>
                                {responseData.text || ''}
                            </pre>
                        )}
                        
                        {helpText}
                    </div>
                </DebugCollapsibleCard> 

                <div className="flex justify-end mt-2"> 
                    {/* Restore checkpoint icon */}
                    {!!checkpointId && (
                        <div className="ml-2 flex-shrink-0">
                            <RestoreCheckpoint 
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