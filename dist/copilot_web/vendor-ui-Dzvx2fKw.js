function getImportPath(filename) {
    const apiBase = window.comfyAPI?.api?.api?.api_base;
    if (apiBase) {
        // 有 API base 时，使用完整路径
        return `${apiBase.substring(1)}/copilot_web/${filename}`;
    } else {
        // 没有 API base 时，使用相对路径（因为所有文件都在同一目录）
        return `./${filename}`;
    }
}
import"./vendor-react-V04_Axys.js";
