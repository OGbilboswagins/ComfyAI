function getImportPath(filename) {
            return `./${filename}`;
        }
            import{j as a}from"./vendor-markdown-CBmlBP6m.js";import{r as d}from"./vendor-react-Dixhfmvb.js";import{W as f,a as n}from"./message-components-wGrDwG40.js";import{c as p}from"./workflowChat-DP6Ois-Q.js";/**
 * @license lucide-react v0.475.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k=[["path",{d:"M9 14 4 9l5-5",key:"102s5s"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11",key:"f3b9sd"}]],w=p("Undo2",k),g=({checkpointId:e,onRestore:c,title:l})=>{const[t,s]=d.useState(!1),i=async()=>{if(!t){s(!0);try{const o=await f.restoreWorkflowCheckpoint(e),r=o.workflow_data_ui||o.workflow_data;r?(o.workflow_data_ui?n.loadGraphData(r):n.loadApiJson(r),console.log(`Restored workflow checkpoint ${e}`),c()):(console.error("No workflow data found in checkpoint"),alert("No workflow data found in checkpoint."))}catch(o){console.error("Failed to restore checkpoint:",o),alert("Failed to restore workflow checkpoint. Please try again.")}finally{s(!1)}}};return a.jsxs("button",{onClick:i,disabled:t,className:`flex flex-row items-center gap-1 p-1 rounded transition-colors ${t?"text-gray-400 cursor-not-allowed":"text-gray-500 hover:!bg-gray-100 hover:!text-gray-600"}`,title:l||`Restore checkpoint ${e}`,children:[a.jsx(w,{size:12}),a.jsx("span",{className:"text-xs",children:"Restore checkpoint"})]})};export{g as R};
