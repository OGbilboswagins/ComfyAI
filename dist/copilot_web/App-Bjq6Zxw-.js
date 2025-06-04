const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["copilot_web/workflowChat-DztaEqXX.js","copilot_web/input.js","copilot_web/vendor-markdown-Dek94WS0.js","copilot_web/vendor-react-V04_Axys.js","copilot_web/message-components-BQDbTDiL.js","copilot_web/assets/input-BFxtFr8c.css","copilot_web/fonts.css"].map(path => {
                        // 判断是否在代理环境下（如 nebula-notebook）
                        let baseUrl = '';
                        try {
                            if (window.location && window.location.pathname.includes('/proxy/')) {
                                // 在代理环境下使用完整路径
                                const protocol = window.location.protocol;
                                const host = window.location.host;
                                const pathname = window.location.pathname;
                                baseUrl = `${protocol}//${host}${pathname}`;
                                // 确保路径以 / 结尾
                                if (!baseUrl.endsWith('/')) {
                                    baseUrl += '/';
                                }
                            } else {
                                // 在本地环境下使用相对路径或API base
                                const apiBase = window.comfyAPI?.api?.api?.api_base;
                                baseUrl = apiBase ? `${apiBase.substring(1)}/` : '';
                            }
                        } catch (e) {
                            console.warn('Failed to get base URL:', e);
                            // 回退到原来的方式
                            const apiBase = window.comfyAPI?.api?.api?.api_base;
                            baseUrl = apiBase ? `${apiBase.substring(1)}/` : '';
                        }
                        
                        return `${baseUrl}${path}`;
                    }))))=>i.map(i=>d[i]);
import{_ as a}from"./input.js";import{j as t}from"./vendor-markdown-Dek94WS0.js";import{r,R as i}from"./vendor-react-V04_Axys.js";import{C as n}from"./message-components-BQDbTDiL.js";/* empty css     */const o={EXPLAIN_NODE:"copilot:explain-node"},d=i.lazy(()=>a(()=>import("./workflowChat-DztaEqXX.js").then(e=>e.w),__vite__mapDeps([0,1,2,3,4,5,6])).then(e=>({default:e.default})));function p(){const[e,s]=r.useState(!1);return r.useEffect(()=>{const l=()=>{s(!0)};return window.addEventListener(o.EXPLAIN_NODE,l),()=>window.removeEventListener(o.EXPLAIN_NODE,l)},[]),t.jsx(n,{children:t.jsx("div",{className:"h-full w-full flex flex-col",children:t.jsx(r.Suspense,{fallback:t.jsx("div",{className:"h-full w-full flex items-center justify-center",children:"Loading..."}),children:t.jsx(d,{visible:!0,triggerUsage:e,onUsageTriggered:()=>s(!1)})})})})}export{p as default};
