/*
 * @Author: 晴知 qingli.hql@alibaba-inc.com
 * @Date: 2024-11-28 10:19:07
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-07-21 16:14:17
 * @FilePath: /comfyui_copilot/ui/src/components/chat/ChatHeader.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { useState, useEffect } from 'react';
import { XIcon, TrashIcon, CogIcon, WarningIcon } from './Icons';
import { ApiKeyModal } from './ApiKeyModal';
import logoImage from '../../../../assets/logo.png';

interface ChatHeaderProps {
    onClose?: () => void;
    onClear?: () => void;
    hasMessages: boolean;
    onHeightResize?: (deltaY: number) => void;
    title?: string;
}

export function ChatHeader({ 
    onClose, 
    onClear, 
    hasMessages, 
    onHeightResize,
    title = "ComfyUI-Copilot"
}: ChatHeaderProps) {
    const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(false);
    const [isResizing, setIsResizing] = useState(false);
    
    const handleApiKeyClick = () => {
        setIsApiKeyModalOpen(true);
    };

    const handleSaveApiKey = (apiKey: string) => {
        localStorage.setItem('chatApiKey', apiKey);
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsResizing(true);
        e.preventDefault();
    };

    const onFeedback = () => {
        window.open('https://docs.google.com/forms/d/e/1FAIpQLSf_SeUpgrZh8sPGwVFXAlsviVXKpsQnyaevcB2VrIqUBYUMKg/viewform?usp=pp_url&entry.838321096=%23%23+%E5%9F%BA%E6%9C%AC%E4%BF%A1%E6%81%AF+%F0%9F%93%8B+Basic+Information%0A%0A%F0%9F%96%A5%EF%B8%8F+%E7%B3%BB%E7%BB%9F%E7%8E%AF%E5%A2%83+/+System+Environment%EF%BC%9A%0A%F0%9F%94%A7+ComfyUI%E7%89%88%E6%9C%AC+/+ComfyUI+Version%EF%BC%9A++%0A%F0%9F%8E%AF+%E4%BD%BF%E7%94%A8%E5%9C%BA%E6%99%AF+/+Use+Case%EF%BC%9A%0A%0A%23%23+%E9%97%AE%E9%A2%98%E6%8F%8F%E8%BF%B0+%E2%9D%93+Problem+Description%0A%0A%F0%9F%90%9B+%E5%85%B7%E4%BD%93%E9%97%AE%E9%A2%98+/+Specific+Issue%EF%BC%9A%0A%F0%9F%94%84+%E5%A4%8D%E7%8E%B0%E6%AD%A5%E9%AA%A4+/+Steps+to+Reproduce%EF%BC%9A%0A%E2%9C%85+%E6%9C%9F%E6%9C%9B%E7%BB%93%E6%9E%9C+/+Expected+Result%EF%BC%9A%0A%E2%9D%8C+%E5%AE%9E%E9%99%85%E7%BB%93%E6%9E%9C+/+Actual+Result%EF%BC%9A%0A%0A%23%23+%E6%94%B9%E8%BF%9B%E5%BB%BA%E8%AE%AE+%F0%9F%92%A1+Improvement+Suggestions%0A%0A%E2%AD%90+%E5%8A%9F%E8%83%BD%E5%BB%BA%E8%AE%AE+/+Feature+Suggestions%EF%BC%9A%0A%F0%9F%8E%A8+%E4%BA%A4%E4%BA%92%E4%BC%98%E5%8C%96+/+UI/UX+Optimization%EF%BC%9A%0A%F0%9F%92%AD+%E5%85%B6%E4%BB%96%E6%84%8F%E8%A7%81+/+Other+Comments%EF%BC%9A', '_blank');
    }

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            const deltaY = e.movementY;
            onHeightResize?.(deltaY);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing, onHeightResize]);

    return (
        <>
            <div className="flex items-center justify-between border-b px-3 py-2 
                        bg-white border-gray-200 sticky top-2 z-10">
                <div className="flex items-center space-x-1">
                    <img 
                        src={`.${logoImage}`}
                        alt="ComfyUI-Copilot Logo" 
                        className="h-7 w-7 -ml-1" 
                    />
                    <h3 className="text-[14px] font-medium text-gray-800">{title}</h3>
                    <button
                        onClick={handleApiKeyClick}
                        className="p-1 bg-white border-none hover:!bg-gray-100 rounded text-gray-500"
                    >
                        <CogIcon className="h-4 w-4" />
                    </button>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        className='inline-flex bg-white border-none items-center justify-center rounded-md p-1.5 text-gray-500 hover:!bg-gray-100'
                        onClick={onFeedback}>
                        {/* <svg className="h-4 w-4" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <g transform="scale(0.0234375)">
                                <path d="M170.666667 896v0.021333c-0.426667 0.021333 0 0.426667 0 2.069334C170.666667 896.426667 170.24 896 170.666667 896z m682.666666-607.488V896H170.666667V170.666667h554.666666V128H170.474667C147.178667 128 128 146.176 128 168.576v729.514667C128 920.448 147.114667 938.666667 170.666667 938.666667h682.666666c23.68 0 42.666667-18.218667 42.666667-40.661334v-609.493333h-42.666667zM618.474667 519.701333a21.312 21.312 0 0 0 29.226666-7.530666l245.333334-416a21.354667 21.354667 0 0 0-36.757334-21.674667l-245.333333 416a21.333333 21.333333 0 0 0 7.530667 29.226667zM298.666667 384.021333h298.666666v-42.666666H298.666667v42.666666z m0 128h170.666666v-42.666666h-170.666666v42.666666z" />
                            </g>
                        </svg> */}
                        <WarningIcon className="h-4 w-4"/>
                    </button>
                    <button
                        className={`inline-flex bg-white border-none items-center justify-center rounded-md p-1.5 
                                 ${hasMessages ? 'text-gray-500 hover:!bg-gray-100' : 'text-gray-300 cursor-not-allowed'}`}
                        disabled={!hasMessages}
                        onClick={onClear}>
                        <TrashIcon className="h-4 w-4" />
                    </button>
                </div>
            </div>

            <ApiKeyModal
                isOpen={isApiKeyModalOpen}
                onClose={() => setIsApiKeyModalOpen(false)}
                onSave={handleSaveApiKey}
                initialApiKey={localStorage.getItem('chatApiKey') || ''}
            />
        </>
    );
} 