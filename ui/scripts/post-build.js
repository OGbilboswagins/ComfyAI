import fs from 'fs';
import path from 'path';
import glob from 'glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// 获取 __dirname 的等效值
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 在 dist/copilot_web 目录下查找包含 __vite__mapDeps 的 JS 文件
const distDir = path.resolve(__dirname, '../../dist/copilot_web');
const files = glob.sync(`${distDir}/**/App-*.js`);

files.forEach(file => {
    console.log('start modify', file)
    let content = fs.readFileSync(file, 'utf-8');

    if (content.includes('__vite__mapDeps')) {
        // 提取新格式的依赖数组，使用非贪婪匹配
        const depsMatch = content.match(/const __vite__mapDeps=\(.*?m\.f=\[(.*?)\]/);
        if (depsMatch && depsMatch[1]) {
            const originalDeps = depsMatch[1];
            
            // 新的智能路径处理逻辑
            const smartPathLogic = `
                        // 智能路径处理逻辑 v2
                        const getBasePath = () => {
                            try {
                                // 优先使用 comfyAPI 提供的 api_base
                                const apiBase = window.comfyAPI?.api?.api?.api_base;
                                if (apiBase && typeof apiBase === 'string') {
                                    console.log('[ComfyUI Copilot] Using comfyAPI api_base:', apiBase);
                                    // 确保 apiBase 格式正确：去除开头的斜杠，确保结尾有斜杠
                                    const cleanApiBase = apiBase.replace(/^\\/+/, '').replace(/\\/+$/, '');
                                    return cleanApiBase ? \`\${cleanApiBase}/\` : '';
                                }
                                
                                // 如果没有 apiBase，根据当前页面 URL 智能判断
                                const currentPath = window.location.pathname;
                                const currentOrigin = window.location.origin;
                                const currentHost = window.location.host;
                                
                                console.log('[ComfyUI Copilot] Current URL info:', {
                                    origin: currentOrigin,
                                    pathname: currentPath,
                                    host: currentHost
                                });
                                
                                // 检查是否是本地开发环境
                                const isLocalDev = /^https?:\\/\\/(localhost|127\\.0\\.0\\.1|0\\.0\\.0\\.0)(:|$)/.test(currentOrigin);
                                
                                // 检查是否是直接的 ComfyUI 环境 (通常有8188端口)
                                const isDirectComfyUI = currentOrigin.includes(':8188') || 
                                                      (isLocalDev && !currentPath.includes('/notebook/'));
                                
                                if (isDirectComfyUI) {
                                    console.log('[ComfyUI Copilot] Detected direct ComfyUI environment');
                                    return '';
                                }
                                
                                // 检查是否在 notebook 环境中 (如 nebula-notebook)
                                const notebookMatch = currentPath.match(/^\\/([^/]+)\\//);
                                if (notebookMatch && notebookMatch[1] && 
                                    (notebookMatch[1].includes('notebook') || 
                                     currentOrigin.includes('notebook') ||
                                     currentOrigin.includes('nebula'))) {
                                    const prefix = notebookMatch[1];
                                    console.log('[ComfyUI Copilot] Detected notebook environment with prefix:', prefix);
                                    return \`\${prefix}/\`;
                                }
                                
                                // 通用路径前缀检测
                                const pathSegments = currentPath.split('/').filter(Boolean);
                                if (pathSegments.length > 0 && pathSegments[0]) {
                                    // 如果第一个路径段不是 copilot_web，可能是需要的前缀
                                    if (pathSegments[0] !== 'copilot_web') {
                                        console.log('[ComfyUI Copilot] Using path-based prefix:', pathSegments[0]);
                                        return \`\${pathSegments[0]}/\`;
                                    }
                                }
                                
                                console.log('[ComfyUI Copilot] Using default empty prefix');
                                return '';
                                
                            } catch (error) {
                                console.error('[ComfyUI Copilot] Error in path detection:', error);
                                return '';
                            }
                        };
                        
                        const prefix = getBasePath();
                        const finalPath = \`\${prefix}\${path}\`;
                        console.log('[ComfyUI Copilot] Resource path mapping:', { original: path, prefix, final: finalPath });
                        return finalPath;`;
            
            // 如果文件中还没有路径转换逻辑，则添加
            if (!content.includes('window.comfyAPI?.api?.api?.api_base')) {
                content = content.replace(
                    /const __vite__mapDeps=.*?\)=>i\.map\(i=>d\[i\]\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}].map(path => {${smartPathLogic}
                    }))))=>i.map(i=>d[i]);`
                );
            } else {
                // 如果已经有路径转换逻辑，替换为新的逻辑
                content = content.replace(
                    /const __vite__mapDeps=\(.*?\)=>i\.map\(i=>d\[i\]\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}].map(path => {${smartPathLogic}
                    }))))=>i.map(i=>d[i]);`
                );
            }

            fs.writeFileSync(file, content, 'utf-8');
            console.log(`Modified ${path.basename(file)} with enhanced path logic`);
        } else {
            console.log(`No deps pattern found in ${path.basename(file)}`);
        }
    } else {
        console.log(`No __vite__mapDeps found in ${path.basename(file)}`);
    }
}); 