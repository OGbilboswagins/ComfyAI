// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { ChangeEvent, KeyboardEvent, useState, useRef, useEffect, ReactNode } from 'react';
import { SendIcon, ImageIcon, PlusIcon, XIcon, StopIcon } from './Icons';
import React from 'react';
import { WorkflowChatAPI } from '../../apis/workflowChatApi';
import { generateUUID } from '../../utils/uuid';

// Debug icon component
const DebugIcon = ({ className }: { className: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 8h-2.81c-.45-.78-1.07-1.45-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5s-.96.06-1.42.17L8.41 3 7 4.41l1.63 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/>
    </svg>
);

interface ChatInputProps {
    input: string;
    loading: boolean;
    onChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
    onSend: () => void;
    onKeyPress: (event: KeyboardEvent) => void;
    onUploadImages: (files: FileList) => void;
    uploadedImages: UploadedImage[];
    onRemoveImage: (imageId: string) => void;
    selectedModel: string;
    onModelChange: (model: string) => void;
    onStop?: () => void;
    onAddDebugMessage?: (message: any) => void;
}

export interface UploadedImage {
    id: string;
    file: File;
    preview: string;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

export function ChatInput({ 
    input, 
    loading, 
    onChange, 
    onSend, 
    onKeyPress, 
    onUploadImages,
    uploadedImages,
    onRemoveImage,
    selectedModel,
    onModelChange,
    onStop,
    onAddDebugMessage,
}: ChatInputProps) {
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [models, setModels] = useState<{
        label: ReactNode; name: string; image_enable: boolean 
}[]>([]);
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea based on content
    useEffect(() => {
        if (textareaRef.current) {
            // Reset height to auto to get the correct scrollHeight
            textareaRef.current.style.height = 'auto';
            // Set the height to scrollHeight to fit all content
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 400)}px`;
        }
    }, [input]);

    // Load models on component mount
    useEffect(() => {
        const loadModels = async () => {
            try {
                const result = await WorkflowChatAPI.listModels();
                setModels(result.models);
            } catch (error) {
                console.error('Failed to load models:', error);
                // Fallback to default models if API fails
                setModels([{
                    "label": "gemini-2.5-flash",
                    "name": "gemini-2.5-flash",
                    "image_enable": true
                },
                {
                    "label": "gpt-4.1",
                    "name": "gpt-4.1-2025-04-14-GlobalStandard",
                    "image_enable": true,
                },
                {
                    "label": "qwen-plus",
                    "name": "qwen-plus",
                    "image_enable": false,
                }]);
            }
        };

        loadModels();
    }, []);

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const invalidFiles: string[] = [];
            const validFiles: File[] = [];

            Array.from(event.target.files).forEach(file => {
                if (!SUPPORTED_FORMATS.includes(file.type)) {
                    invalidFiles.push(`${file.name} (unsupported format)`);
                } else if (file.size > MAX_FILE_SIZE) {
                    invalidFiles.push(`${file.name} (exceeds 5MB)`);
                } else {
                    validFiles.push(file);
                }
            });

            if (invalidFiles.length > 0) {
                alert(`The following files couldn't be uploaded:\n${invalidFiles.join('\n')}`);
            }

            if (validFiles.length > 0) {
                const dataTransfer = new DataTransfer();
                validFiles.forEach(file => dataTransfer.items.add(file));
                onUploadImages(dataTransfer.files);
            }
        }
    };

    const handleDebugClick = () => {
        if (onAddDebugMessage) {
            const debugMessage = {
                id: generateUUID(),
                role: 'ai' as const,
                content: JSON.stringify({
                    text: "Would you like me to help you debug the current workflow on the canvas?",
                    ext: []
                }),
                format: 'debug_guide' as const,
                name: 'Assistant'
            };
            onAddDebugMessage(debugMessage);
        }
    };

    return (
        <div className={`relative ${uploadedImages.length > 0 ? 'mt-12' : ''}`}>
            {/* 已上传图片预览 */}
            {uploadedImages.length > 0 && (
                <div className="absolute -top-10 left-0 flex gap-2">
                    {uploadedImages.map(image => (
                        <div key={image.id} className="relative group">
                            <img 
                                src={image.preview} 
                                alt="uploaded" 
                                className="w-8 h-8 rounded object-cover"
                            />
                            <button
                                onClick={() => onRemoveImage(image.id)}
                                className="absolute -top-1 -right-1 bg-white border-none text-gray-500 rounded-full p-0.5
                                         opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <XIcon className="w-3 h-3" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <textarea
                ref={textareaRef}
                onChange={onChange}
                onKeyDown={(e: KeyboardEvent) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        if (e.nativeEvent.isComposing) {
                            return;
                        }
                        e.preventDefault();
                        if (input.trim() !== '') {
                            onSend();
                        }
                    }
                    onKeyPress(e);
                }}
                value={input}
                placeholder="Type your message..."
                className="w-full min-h-[80px] max-h-[400px] resize-none rounded-md border 
                         border-gray-200 px-3 py-2 pr-12 pb-10 text-[14px] shadow-sm 
                         focus:outline-none focus:ring-2 focus:ring-blue-500 
                         focus:border-transparent bg-white transition-all 
                         duration-200 text-gray-700 overflow-y-auto"
                style={{ height: '80px' }}
            />

            {/* Bottom toolbar */}
            <div className="absolute bottom-2 left-3 right-12 flex items-center gap-2 
                          bg-white border-t border-gray-100 pt-1">
                {/* Model selector dropdown */}
                <select
                    value={selectedModel}
                    onChange={(e) => onModelChange(e.target.value)}
                    className="px-1.5 py-0.5 text-xs rounded-md 
                             border border-gray-200 bg-white text-gray-700
                             focus:outline-none focus:ring-2 focus:ring-blue-500
                             focus:border-transparent hover:bg-gray-50
                             transition-colors border-0"
                >
                    {models.map((model) => (
                        <option value={model.name} key={model.name}>{model.label}</option>
                    ))}
                </select>

                {/* Upload image button */}
                <button
                    type="button"
                    onClick={() => setShowUploadModal(true)}
                    disabled={!models.find(model => model.name === selectedModel)?.image_enable}
                    className={`p-1.5 text-gray-500 bg-white border-none
                             hover:bg-gray-100 hover:text-gray-600 
                             transition-all duration-200 outline-none
                             ${!models.find(model => model.name === selectedModel)?.image_enable ? 'opacity-50 cursor-not-allowed' : ''}`}>
                    <ImageIcon className="h-4 w-4" />
                </button>
            </div>

            {/* Send button */}
            <button
                type="submit"
                onClick={loading ? onStop : onSend}
                disabled={loading ? false : input.trim() === ''}
                className="absolute bottom-3 right-3 p-2 rounded-md text-gray-500 bg-white border-none 
                         hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50 
                         transition-all duration-200 active:scale-95">
                {loading ? (
                    <StopIcon className="h-5 w-5 text-red-500 hover:text-red-600" />
                ) : (
                    <SendIcon className="h-5 w-5 group-hover:translate-x-1" />
                )}
            </button>

            {/* Debug button */}
            <button
                type="button"
                onClick={handleDebugClick}
                className="absolute bottom-3 right-14 p-2 rounded-md text-gray-500 bg-white border-none 
                         hover:bg-gray-100 hover:text-gray-600 
                         transition-all duration-200 active:scale-95"
                title="Debug workflow">
                <DebugIcon className="h-5 w-5" />
            </button>

            {/* 上传图片模态框 */}
            {showUploadModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-96 relative">
                        <button 
                            onClick={() => setShowUploadModal(false)}
                            className="absolute top-2 right-2 bg-white border-none text-gray-500 hover:text-gray-700"
                        >
                            <XIcon className="w-5 h-5" />
                        </button>
                        
                        <h3 className="text-lg text-gray-800 font-medium mb-4">Upload Images</h3>
                        
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8
                                      flex flex-col items-center justify-center gap-4
                                      hover:border-blue-500 transition-colors cursor-pointer"
                             onClick={() => fileInputRef.current?.click()}
                        >
                            <PlusIcon className="w-8 h-8 text-gray-400" />
                            <div className="text-center">
                                <p className="text-sm text-gray-500 mb-2">
                                    Click to upload images or drag and drop
                                </p>
                                <p className="text-xs text-gray-400">
                                    Supported formats: JPG, PNG, GIF, WebP
                                </p>
                                <p className="text-xs text-gray-400">
                                    Max file size: 5MB
                                </p>
                            </div>
                        </div>

                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            accept={SUPPORTED_FORMATS.join(',')}
                            onChange={handleFileChange}
                            className="hidden"
                        />

                        {/* 预览区域 */}
                        {uploadedImages.length > 0 && (
                            <div className="mt-4 grid grid-cols-3 gap-2">
                                {uploadedImages.map(image => (
                                    <div key={image.id} className="relative group">
                                        <img 
                                            src={image.preview} 
                                            alt="preview" 
                                            className="w-full h-20 object-cover rounded"
                                        />
                                        <button
                                            onClick={() => onRemoveImage(image.id)}
                                            className="absolute -top-1 -right-1 bg-white border-none text-gray-500 
                                                     rounded-full p-0.5 opacity-0 group-hover:opacity-100 
                                                     transition-opacity"
                                        >
                                            <XIcon className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="mt-4 flex justify-end gap-2">
                            <button
                                onClick={() => setShowUploadModal(false)}
                                className="px-4 py-2 text-sm font-medium text-gray-700 
                                         bg-white border border-gray-300 rounded-md 
                                         hover:bg-gray-50"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
} 