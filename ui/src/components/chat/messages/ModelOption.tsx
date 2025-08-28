import { useEffect, useState } from "react";
import { app } from "../../../utils/comfyapp";
import Modal from "../../ui/Modal";

interface IProps {
  modelSuggests: any[]
  showTitle?: boolean
}

const TITLE_ZH = '发现模型缺失，推荐下载以下模型。'
const TITLE_EN = 'Missing models detected. We recommend downloading the following models.'

const TH_ZH = {
  name: '名称',
  dir: '模型下载存放目录',
  option: '操作'
}
const TH_EN = {
  name: 'Name',
  dir: 'Models download directory',
  option: 'Option'
}

const ModelOption: React.FC<IProps> = (props) => {
  const { modelSuggests, showTitle = true } = props
  const browserLanguage = app.extensionManager.setting.get('Comfy.Locale');
  const [modelPaths, setModelPaths] = useState<string[] | null>(null)
  const [downloadedMap, setDownloadedMap] = useState<Record<string, boolean>>({})
  const [selectedPathMap, setSelectedPathMap] = useState<Record<string, string>>({})
  const [modalContent, setModalContent] = useState<string | null>(null)
  const thMap = browserLanguage === 'zh' ? TH_ZH : TH_EN

  useEffect(() => {
    (
      async () => {
        const response = await fetch('/api/model-paths')
        const data = await response.json()
        setModelPaths(data?.data?.paths || [])
        let downloads: Record<string, boolean> = {}
        let selectedPaths: Record<string, string> = {}
        modelSuggests?.forEach(item => { 
          const id = `${item.Path}/${item.Name}`
          downloads[id] = false
          const index = data?.data?.paths?.findIndex((path: string) => item.model_type === path)
          selectedPaths[id] = data?.data?.paths?.[index === -1 ? 0 : index] || ''
        })
        setDownloadedMap(downloads)
        setSelectedPathMap(selectedPaths)
      }
    )()
  }, [])

  const handleDownload = async (id: string, type: string) => {
    setDownloadedMap(prev => ({
      ...prev,
      [id]: true
    }))
    const modelType = !!type && type !== '' ? type : selectedPathMap[id]
    let body: Record<string, string> = {
      model_id: id,
      model_type: modelType,
    }
    if (!!selectedPathMap[id] && selectedPathMap[id] !== '') {
      body['dest_dir'] = selectedPathMap[id]
    }
    const response = await fetch('/api/download-model', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    const res = await response.json()
    if (!res.success) {
      setModalContent(res.message || 'Download Model Failed!')
      setDownloadedMap(prev => ({
        ...prev,
        [id]: false
      }))
    }
    console.log('response--->',response.json())
  }

  const handleSelectedPath = (id: string, path: string) => {
    setSelectedPathMap(prev => ({
      ...prev,
      [id]: path
    }))
  }

  if (!modelPaths) 
    return null

  return <div className="mt-4 w-full">
    {
      showTitle && <h3 className="text-xl text-gray-900 font-bold">
        {browserLanguage === 'zh' ? TITLE_ZH : TITLE_EN}
      </h3>
    }
    <table className="w-full border-gray-300">
      <thead>
        <tr>
          <th className="px-4 py-1 border border-gray-300">{thMap.name}</th>
          <th className="px-4 py-1 border border-gray-300">{thMap.dir}</th>
          <th className="px-4 py-1 border border-gray-300">{thMap.option}</th>
        </tr>
      </thead>
      <tbody>
        {
          modelSuggests.map((item, index) => (
              <tr key={index}>
                <td className="px-4 py-1 border border-gray-300 text-center">{item.Name}</td>
                <td className="px-4 py-1 border border-gray-300 text-center">
                  <select
                    value={selectedPathMap[`${item.Path}/${item.Name}`]}
                    onChange={(e) => handleSelectedPath(`${item.Path}/${item.Name}`, e.target.value)}
                    className="px-1.5 py-0.5 text-xs rounded-md bg-gray-100
                            text-gray-700 focus:outline-none focus:ring-2 
                            focus:ring-blue-500 hover:!bg-gray-50"
                  >
                    {modelPaths.map((path) => (
                        <option value={path} key={path}>{path}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-1 border border-gray-300 text-center">
                  <div className="w-full h-full flex justify-center items-center">
                    <button 
                      className="text-gray-900 hover:!text-blue-500 disabled:!text-gray-300 flex justify-center items-center"
                      disabled={downloadedMap[`${item.Path}/${item.Name}`]}
                      onClick={() => handleDownload(`${item.Path}/${item.Name}`, item?.model_type || '')}
                    >
                      <svg viewBox="0 0 1024 1024" className="w-5 h-5" fill='currentColor'>
                        <path d="M1022.955204 522.570753c0 100.19191-81.516572 181.698249-181.718715 181.698249l-185.637977 0c-11.2973 0-20.466124-9.168824-20.466124-20.466124 0-11.307533 9.168824-20.466124 20.466124-20.466124l185.637977 0c77.628008 0 140.786467-63.148226 140.786467-140.766001 0-77.423347-62.841234-140.448776-140.203182-140.766001-0.419556 0.030699-0.818645 0.051165-1.217734 0.061398-5.945409 0.143263-11.686157-2.292206-15.687284-6.702656-4.001127-4.400217-5.894244-10.335393-5.167696-16.250102 1.330298-10.806113 1.944282-19.760043 1.944282-28.192086 0-60.763922-23.658839-117.884874-66.617234-160.833035-42.968627-42.968627-100.089579-66.617234-160.843268-66.617234-47.368844 0-92.742241 14.449084-131.208321 41.781592-37.616736 26.738991-65.952084 63.700811-81.925894 106.884332-2.425236 6.538927-8.012488 11.399631-14.827707 12.893658-6.815219 1.483794-13.927197-0.603751-18.859533-5.54632-19.289322-19.330254-44.943608-29.972639-72.245418-29.972639-56.322773 0-102.146425 45.813419-102.146425 102.125959 0 0.317225 0.040932 0.982374 0.092098 1.627057 0.061398 0.920976 0.122797 1.831718 0.153496 2.762927 0.337691 9.465582-5.863545 17.928325-15.001669 20.455891-32.356942 8.933463-61.541635 28.550243-82.181721 55.217602-21.305235 27.516704-32.571836 60.508096-32.571836 95.41307 0 86.244246 70.188572 156.422585 156.443052 156.422585l169.981393 0c11.2973 0 20.466124 9.15859 20.466124 20.466124 0 11.2973-9.168824 20.466124-20.466124 20.466124l-169.981393 0c-108.828614 0-197.3753-88.536452-197.3753-197.354833 0-44.053332 14.223956-85.712127 41.126676-120.473839 22.809495-29.460985 53.897537-52.086285 88.710414-64.816215 5.065366-74.322729 67.149353-133.2447 142.751215-133.2447 28.386514 0 55.504128 8.217149 78.651314 23.52581 19.657712-39.868009 48.842405-74.169233 85.497233-100.212376 45.434795-32.295544 99.004875-49.354058 154.918325-49.354058 71.692832 0 139.087778 27.915793 189.782368 78.600149 50.694589 50.694589 78.610382 118.089535 78.610382 189.782368 0 3.704368-0.102331 7.470135-0.296759 11.368932C952.633602 352.568894 1022.955204 429.511287 1022.955204 522.570753z" p-id="4439">
                        </path>
                        <path d="M629.258611 820.711014l-102.023628 102.013395c-3.990894 4.001127-9.230222 5.996574-14.46955 5.996574s-10.478655-1.995447-14.46955-5.996574l-102.023628-102.013395c-7.992021-7.992021-7.992021-20.947078 0-28.939099s20.947078-8.002254 28.939099 0l67.087954 67.077721 0-358.699522c0-11.2973 9.15859-20.466124 20.466124-20.466124 11.307533 0 20.466124 9.168824 20.466124 20.466124l0 358.699522 67.087954-67.077721c7.992021-8.002254 20.947078-7.992021 28.939099 0S637.250632 812.718993 629.258611 820.711014z" p-id="4440">
                        </path>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
          ))
        }
      </tbody>
    </table>
    <Modal open={!!modalContent && modalContent !== ''} onClose={() => setModalContent(null)}>
      <p>{modalContent}</p>
    </Modal>
  </div>
}

export default ModelOption