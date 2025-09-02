import { app } from "../utils/comfyapp"
import showcases from '../../../public/showcase/showcase.json';
import showcases_en from '../../../public/showcase/showcase_en.json';
import { useMemo } from "react";

const useLanguage = () => {
    const language = app.extensionManager.setting.get('Comfy.Locale')

    const languageData = useMemo(() => {
        let showcase_title = ''
        let showcase_subtitle = ''
        let showcase_list = showcases_en
        switch (language) {
          case 'zh':
            showcase_title = '欢迎使用ComfyUI Copilot!'
            showcase_subtitle = '已有 2600+ 开发者加入🚀，您的Star是我们持续维护和升级的动力， 👉🏻立即Star。'
            showcase_list = showcases
            break;
          case 'en':
          default:
            showcase_title = 'Welcome to ComfyUI Copilot!'
            showcase_subtitle = '2600 + developers have joined🚀, Your Star is the driving force for our continuous maintenance and upgrade, 👉🏻Go Star.'
            showcase_list = showcases_en
            break;
        }
        return {
          showcase_title,
          showcase_subtitle,
          showcase_list
        };
    }, [language])

    return languageData
}

export default useLanguage