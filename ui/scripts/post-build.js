/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-02-17 20:53:45
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-06-04 17:16:22
 * @FilePath: /comfyui_copilot/ui/scripts/post-build.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
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
            
            // 如果文件中还没有路径转换逻辑，则添加
            if (!content.includes('window.location.protocol')) {
                content = content.replace(
                    /const __vite__mapDeps=.*?\)=>i\.map\(i=>d\[i\]\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}].map(path => {
                        // 判断是否在代理环境下（如 nebula-notebook）
                        let baseUrl = '';
                        try {
                            if (window.location && window.location.pathname.includes('/proxy/')) {
                                // 在代理环境下使用完整路径
                                const protocol = window.location.protocol;
                                const host = window.location.host;
                                const pathname = window.location.pathname;
                                baseUrl = \`\${protocol}//\${host}\${pathname}\`;
                                // 确保路径以 / 结尾
                                if (!baseUrl.endsWith('/')) {
                                    baseUrl += '/';
                                }
                            } else {
                                // 在本地环境下使用相对路径或API base
                                const apiBase = window.comfyAPI?.api?.api?.api_base;
                                baseUrl = apiBase ? \`\${apiBase.substring(1)}/\` : '';
                            }
                        } catch (e) {
                            console.warn('Failed to get base URL:', e);
                            // 回退到原来的方式
                            const apiBase = window.comfyAPI?.api?.api?.api_base;
                            baseUrl = apiBase ? \`\${apiBase.substring(1)}/\` : '';
                        }
                        
                        return \`\${baseUrl}\${path}\`;
                    }))))=>i.map(i=>d[i]);`
                );
            } else {
                // 如果已经有路径转换逻辑，只替换依赖数组部分
                content = content.replace(
                    /const __vite__mapDeps=\(.*?\)=>i\.map\(i=>d\[i\]\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}])))=>i.map(i=>d[i]);`
                );
            }

            fs.writeFileSync(file, content, 'utf-8');
            console.log(`Modified ${path.basename(file)}`);
        } else {
            console.log(`No deps pattern found in ${path.basename(file)}`);
        }
    } else {
        console.log(`No __vite__mapDeps found in ${path.basename(file)}`);
    }
}); 