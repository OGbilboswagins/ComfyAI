import { app } from "../../utils/comfyapp";

interface IProps {
  children?: React.ReactNode;
  className?: string;
  borderClassName?: string;
}

const BeautifyCard: React.FC<IProps> = ({ children, className, borderClassName }) => {
  const isDark = app.extensionManager.setting.get('Comfy.ColorPalette') === 'dark';
  return (
    <div className='sticky w-full'>
      <div className={`relative ${className || ''} ${isDark ? 'beautify-card-dark' : 'beautify-card-light'}`}>
        <div className={`card-border ${borderClassName || ''}`}/>
        {
          children
        }
      </div>
    </div>
  );
};

export default BeautifyCard;