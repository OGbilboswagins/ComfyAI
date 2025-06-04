/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-02-17 20:53:45
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-06-04 19:22:30
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
            if (!content.includes('window.comfyAPI?.api?.api?.api_base')) {
                content = content.replace(
                    /const __vite__mapDeps=.*?\)=>i\.map\(i=>d\[i\]\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}].map(path => {
                        const apiBase = window.comfyAPI?.api?.api?.api_base;
                        const prefix = apiBase ? \`\${apiBase.substring(1)}/\` : '';
                        return \`\${prefix}\${path}\`;
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
    }
    
    // 处理直接的 import() 调用
    if (content.includes('import("./')) {
        // 添加路径转换函数（如果还没有）
        if (!content.includes('function getImportPath')) {
            const pathTransformFunction = `
const getImportPath = (relativePath) => {
    const apiBase = window.comfyAPI?.api?.api?.api_base;
    if (apiBase) {
        // 有 API base 时，使用绝对路径
        const prefix = apiBase.substring(1); // 移除开头的 /
        return \`/\${prefix}/copilot_web/\${relativePath}\`;
    } else {
        // 没有 API base 时，使用相对路径
        return \`./\${relativePath}\`;
    }
};`;
            content = pathTransformFunction + content;
        }
        
        // 替换所有直接的 import() 调用，保留相对路径前缀
        content = content.replace(/import\("\.\/([^"]+)"\)/g, 'import(getImportPath("$1"))');
        
        fs.writeFileSync(file, content, 'utf-8');
        console.log(`Modified direct import() calls in ${path.basename(file)}`);
    }
    
    if (!content.includes('__vite__mapDeps') && !content.includes('import("./')) {
        console.log(`No __vite__mapDeps or direct imports found in ${path.basename(file)}`);
    }
}); 