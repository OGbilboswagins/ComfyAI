const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["copilot_web/workflowChat-DztaEqXX.js","copilot_web/input.js","copilot_web/vendor-markdown-Dek94WS0.js","copilot_web/vendor-react-V04_Axys.js","copilot_web/message-components-BQDbTDiL.js","copilot_web/assets/input-BFxtFr8c.css","copilot_web/fonts.css"].map(path => {
                        // 智能路径处理逻辑 v2
                        const getBasePath = () => {
                            try {
                                // 优先使用 comfyAPI 提供的 api_base
                                const apiBase = window.comfyAPI?.api?.api?.api_base;
                                if (apiBase && typeof apiBase === 'string') {
                                    console.log('[ComfyUI Copilot] Using comfyAPI api_base:', apiBase);
                                    // 确保 apiBase 格式正确：去除开头的斜杠，确保结尾有斜杠
                                    const cleanApiBase = apiBase.replace(/^\/+/, '').replace(/\/+$/, '');
                                    return cleanApiBase ? `${cleanApiBase}/` : '';
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
                                const isLocalDev = /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:|$)/.test(currentOrigin);
                                
                                // 检查是否是直接的 ComfyUI 环境 (通常有8188端口)
                                const isDirectComfyUI = currentOrigin.includes(':8188') || 
                                                      (isLocalDev && !currentPath.includes('/notebook/'));
                                
                                if (isDirectComfyUI) {
                                    console.log('[ComfyUI Copilot] Detected direct ComfyUI environment');
                                    return '';
                                }
                                
                                // 检查是否在 notebook 环境中 (如 nebula-notebook)
                                const notebookMatch = currentPath.match(/^\/([^/]+)\//);
                                if (notebookMatch && notebookMatch[1] && 
                                    (notebookMatch[1].includes('notebook') || 
                                     currentOrigin.includes('notebook') ||
                                     currentOrigin.includes('nebula'))) {
                                    const prefix = notebookMatch[1];
                                    console.log('[ComfyUI Copilot] Detected notebook environment with prefix:', prefix);
                                    return `${prefix}/`;
                                }
                                
                                // 通用路径前缀检测
                                const pathSegments = currentPath.split('/').filter(Boolean);
                                if (pathSegments.length > 0 && pathSegments[0]) {
                                    // 如果第一个路径段不是 copilot_web，可能是需要的前缀
                                    if (pathSegments[0] !== 'copilot_web') {
                                        console.log('[ComfyUI Copilot] Using path-based prefix:', pathSegments[0]);
                                        return `${pathSegments[0]}/`;
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
                        const finalPath = `${prefix}${path}`;
                        console.log('[ComfyUI Copilot] Resource path mapping:', { original: path, prefix, final: finalPath });
                        return finalPath;
                    }))))=>i.map(i=>d[i]);
import{_ as a}from"./input.js";import{j as t}from"./vendor-markdown-Dek94WS0.js";import{r,R as i}from"./vendor-react-V04_Axys.js";import{C as n}from"./message-components-BQDbTDiL.js";/* empty css     */const o={EXPLAIN_NODE:"copilot:explain-node"},d=i.lazy(()=>a(()=>import("./workflowChat-DztaEqXX.js").then(e=>e.w),__vite__mapDeps([0,1,2,3,4,5,6])).then(e=>({default:e.default})));function p(){const[e,s]=r.useState(!1);return r.useEffect(()=>{const l=()=>{s(!0)};return window.addEventListener(o.EXPLAIN_NODE,l),()=>window.removeEventListener(o.EXPLAIN_NODE,l)},[]),t.jsx(n,{children:t.jsx("div",{className:"h-full w-full flex flex-col",children:t.jsx(r.Suspense,{fallback:t.jsx("div",{className:"h-full w-full flex items-center justify-center",children:"Loading..."}),children:t.jsx(d,{visible:!0,triggerUsage:e,onUsageTriggered:()=>s(!1)})})})})}export{p as default};
