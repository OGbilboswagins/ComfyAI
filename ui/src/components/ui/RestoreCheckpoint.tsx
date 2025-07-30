import { Undo2 } from "lucide-react";
import { useState } from "react";
import { WorkflowChatAPI } from "../../apis/workflowChatApi";
import { app } from "../../utils/comfyapp";

const RestoreCheckpoint = ({ checkpointId, onRestore, title }: { checkpointId: number; onRestore: () => void; title?: string }) => {
  const [isRestoring, setIsRestoring] = useState(false);

  const handleRestore = async () => {
      if (isRestoring) return;
      
      setIsRestoring(true);
      try {
          const checkpointData = await WorkflowChatAPI.restoreWorkflowCheckpoint(checkpointId);
          
          // Use UI format if available, otherwise use API format
          const workflowToLoad = checkpointData.workflow_data_ui || checkpointData.workflow_data;
          
          if (workflowToLoad) {
              // Load workflow to canvas
              if (checkpointData.workflow_data_ui) {
                  // UI format - use loadGraphData
                  app.loadGraphData(workflowToLoad);
              } else {
                  // API format - use loadApiJson
                  app.loadApiJson(workflowToLoad);
              }
              
              console.log(`Restored workflow checkpoint ${checkpointId}`);
              onRestore();
          } else {
              console.error('No workflow data found in checkpoint');
              alert('No workflow data found in checkpoint.');
          }
      } catch (error) {
          console.error('Failed to restore checkpoint:', error);
          alert('Failed to restore workflow checkpoint. Please try again.');
      } finally {
          setIsRestoring(false);
      }
  };

  return (
      <button
          onClick={handleRestore}
          disabled={isRestoring}
          className={`flex flex-row items-center gap-1 p-1 rounded transition-colors ${
              isRestoring 
                  ? 'text-gray-400 cursor-not-allowed' 
                  : 'text-gray-500 hover:!bg-gray-100 hover:!text-gray-600'
          }`}
          title={title || `Restore checkpoint ${checkpointId}`}
      >
          <Undo2 size={12} />
          <span className="text-xs">Restore checkpoint</span>
      </button>
  );
};

export default RestoreCheckpoint;