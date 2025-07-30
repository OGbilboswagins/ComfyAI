/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-07-30 16:30:22
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-07-30 17:24:40
 * @FilePath: /comfyui_copilot/ui/src/components/ui/DebugCollapsibleCard.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface IProps {
  title?: string | React.ReactNode;
  isWorkflowUpdate?: boolean;
  className?: string;
  children: React.ReactNode;
}

const DebugCollapsibleCard: React.FC<IProps> = (props) => {
  const { title = '', isWorkflowUpdate = false,className = '', children } = props;
  
  const [isOpen, setIsOpen] = useState(false);

  const color = isWorkflowUpdate 
  ? '#166534'
  : '#E5E7EB';
  
  return (
    <div className={`relative shadow-gray-200 dark:shadow-gray-600 rounded-lg p-2 overflow-hidden ${className} ${!isOpen ? 'h-[200px]' : 'h-auto'}`}>
      <div className="flex justify-between items-center">
        <div>
        {
          typeof title === 'string' ? <h3 className="text-sm text-gray-900 dark:text-white font-medium">{title}</h3> : title
        }
        </div>
        <button
          onClick={() => {
            console.log('setOpen--->')
            setIsOpen(!isOpen)
          }}
        >
          {
            isOpen ? <ChevronUp color={color} /> : <ChevronDown color={color} />
          }
        </button>
      </div>
      <div className="dark:border-gray-700">
      {
        children
      }
      </div>
      {
        !isOpen && <div className="absolute bottom-0 left-0 right-0 h-40 w-full z-5 bg-gradient-to-t from-[#fff] to-transparent pointer-events-none" />
      }
    </div>
  )
}

export default DebugCollapsibleCard;