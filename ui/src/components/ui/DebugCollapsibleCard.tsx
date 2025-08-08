/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-07-30 16:30:22
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-07-30 17:24:40
 * @FilePath: /comfyui_copilot/ui/src/components/ui/DebugCollapsibleCard.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { ChevronDown, ChevronUp } from "lucide-react";
import { useEffect, useState } from "react";

interface IProps {
  title?: string | React.ReactNode;
  isWorkflowUpdate?: boolean;
  className?: string;
  onFinishLoad?: () => void;
  children: React.ReactNode;
}

const DebugCollapsibleCard: React.FC<IProps> = (props) => {
  const { title = '', isWorkflowUpdate = false, className = '', onFinishLoad, children } = props;
  
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    onFinishLoad?.();
  }, []);
  
  return (
    <div className={`relative rounded-lg flex flex-col debug-collapsible-card ${className} ${!isOpen ? 'h-[200px]' : ''}`}>
      <div className="card-border rounded-lg" />
      <div className="flex flex-1 justify-between items-center pb-2 border-b border-[#29292f]">
        <div>
        {
          typeof title === 'string' ? <h3 className="text-sm text-[#fff] font-medium">{title}</h3> : title
        }
        </div>
        <button
          onClick={() => {
            setIsOpen(!isOpen)
          }}
        >
          {
            isOpen ? <ChevronUp color={'#E5E7EB'} /> : <ChevronDown color={'#E5E7EB'} />
          }
        </button>
      </div>
      <div className="overflow-hidden">
      {
        children
      }
      </div>
      {/* {
        !isOpen && <div className="absolute bottom-0 left-0 right-0 h-12 w-full z-5 bg-debug-collapsible-card-bg pointer-events-none" />
      } */}
    </div>
  )
}

export default DebugCollapsibleCard;