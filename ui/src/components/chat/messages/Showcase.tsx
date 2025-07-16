import showcases from '../../../../../public/showcase/showcase.json';
import showcases_en from '../../../../../public/showcase/showcase_en.json';
import { useChatContext } from '../../../context/ChatContext';
import { app } from '../../../utils/comfyapp';
import { generateUUID } from '../../../utils/uuid';
import { BaseMessage } from './BaseMessage';

const OFFSET = 2;

const Showcase: React.FC = () => {
  const { dispatch, isAutoScroll, showcasIng } = useChatContext();

  const doStreamString = (data: any, isUser: boolean = false, cb: () => void = () => {}) => {
    let end = 0;
    const messageId = generateUUID();
    const func = (isFirst: boolean = false) => {
      if (!showcasIng.current)
        return;
      end += OFFSET
      const isString = typeof data === 'string';
      const str = isString ? data : data?.text || '';
      const message = isUser ? {
        id: messageId,
        role: "user",
        content: str.slice(0, end)
      } : {
        id: messageId,
        role: "ai",
        content: (end > str.length && !!data?.ext) ? 
          JSON.stringify({
            text: str.slice(0, end),
            ext: data?.ext,
          }) : JSON.stringify({
            text: str.slice(0, end)
          }
        ),
        finished: end > str.length,
        format:"markdown",
        name: "Assistant"
      }
      const type = isFirst ? 'ADD_MESSAGE' : 'UPDATE_MESSAGE';
      dispatch({ type, payload: message });
      if (end <= str.length) {
        setTimeout(() => {
          func()
        }, isUser ? 10 : 50)
      } else {
        setTimeout(() => {
          cb()
        }, 500)
      }
    }
    func(true)
  }

  const addQuestion = (question: string, cb: () => void) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    doStreamString(question, true, cb);
  }

  const addAnswer = (data: any, cb: () => void) => {
    dispatch({ type: 'SET_LOADING', payload: false });
    doStreamString(data, false, cb);
  }

  const getShowcaes = () => {
    const language = app.extensionManager.setting.get('Comfy.Locale')
    let list = showcases_en
    let title = 'welcome to ComfyUI Copilot!'
    switch (language) {
      case 'zh':
        title = '欢迎使用ComfyUI Copilot!'
        list = showcases
        break;
      case 'en':
      default:
        title = 'welcome to ComfyUI Copilot!'
        list = showcases_en
        break;
    }
    return {
      title,
      list
    };
  }

  return <BaseMessage name='showcase'>
    <div className='bg-gray-100 p-4 rounded-lg'>
      <div className='text-xl text-gray-900 font-extrabold'>
        {getShowcaes()?.title}
      </div>
      {
        getShowcaes()?.list?.map((item, index) => <div 
          className='flex mt-2'
          key={index.toString()}
          onClick={() => {
            isAutoScroll.current = true
            showcasIng.current = true
            const messages = item.messages || []
            let index = 0;
            const func = () => {
              if (index < messages.length) {
                const message = messages[index];
                if (message.role === 'user') {
                  addQuestion(message.content, func);
                } else {
                  addAnswer(JSON.parse(message.content || '{}') || '', func);
                }
                index++;
              }
            }
            func()
          }}
        >
          <span className='text-sm text-gray-900 font-normal border border-gray-900 rounded-md px-2 py-1'>
            {item.name}
          </span>
        </div>)
      }
    </div>
  </BaseMessage>
}

export default Showcase;