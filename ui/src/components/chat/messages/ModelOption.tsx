import { useEffect, useState } from "react";
import { app } from "../../../utils/comfyapp";
import Modal from "../../ui/Modal";
import { useChatContext } from "../../../context/ChatContext";
import LoadingIcon from "../../ui/LoadingIcon";
import { Table, type TableProps } from 'antd';
import TableEmpty from "../../ui/TableEmpty";
interface IProps {
  modelSuggests: any[]
  loading?: boolean
  showTitle?: boolean
  showPagination?: boolean
}

type ColumnsType<T extends object> = TableProps<T>['columns'];

type DataType = {
  Id: number
  Name: string
  Path: string
  ChineseName?: string
  source_model_type?: string
  source_missing_model?: string
  source_keyword?: string
  model_type?: string
}

const TITLE_ZH = '发现模型缺失，推荐下载以下模型。'
const TITLE_EN = 'Missing models detected. We recommend downloading the following models.'

const TH_ZH = {
  name: '模型ID',
  dir: '模型下载存放目录',
  action: '操作'
}
const TH_EN = {
  name: 'Model ID',
  dir: 'Models download directory',
  action: 'Action'
}

const ModelOption: React.FC<IProps> = (props) => {
  const { modelSuggests, loading = false, showTitle = true, showPagination = true } = props
  const { modelDownloadMap, addDownloadId } = useChatContext()

  const browserLanguage = app.extensionManager.setting.get('Comfy.Locale');
  const [modelPaths, setModelPaths] = useState<string[] | null>(null)
  const [selectedPathMap, setSelectedPathMap] = useState<Record<number, string>>({})
  const [modalContent, setModalContent] = useState<string | null>(null)
  const thMap = browserLanguage === 'zh' ? TH_ZH : TH_EN

  const getModelPaths = async () => {
    const response = await fetch('/api/model-paths')
    const res = await response.json()
    setModelPaths(res?.data?.paths || [])
  }

  useEffect(() => {
    getModelPaths()
  }, [])
  
  useEffect(() => {
    if (!modelPaths || modelPaths.length === 0) 
      return
    let selectedPaths: Record<number, string> = {}
    modelSuggests?.forEach(item => { 
      const index = modelPaths.findIndex((path: string) => item.model_type === path)
      selectedPaths[item.Id] = modelPaths[index === -1 ? 0 : index] || ''
    })
    setSelectedPathMap(selectedPaths)
  }, [modelSuggests, modelPaths])

  const handleDownload = async (id: number, modelId: string, modelType: string) => {
    let body: Record<string, string | number> = {
      id,
      model_id: modelId,
      model_type: !!modelType && modelType !== '' ? modelType : selectedPathMap[id],
    }
    // if (!!selectedPathMap[id] && selectedPathMap[id] !== '') {
    //   body['dest_dir'] = selectedPathMap[id]
    // }
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
    } else {
      addDownloadId(res.data.download_id)
    }
  }

  const handleSelectedPath = (id: number, path: string) => {
    setSelectedPathMap(prev => ({
      ...prev,
      [id]: path
    }))
  }

  const renderDownloadProgress = (status: string) => {
    if (status === 'completed') {
      return <svg className="w-5 h-5" viewBox="0 0 1024 1024" fill="#13d320">
        <path d="M198.920606 353.438906l294.89452 398.030819-141.866143 105.106304-294.89452-398.030819 141.866143-105.106304Z">
        </path>
        <path d="M292.668567 679.383279l612.100893-449.37515 104.488343 142.3252-612.100893 449.37515-104.488343-142.3252Z">
        </path>
      </svg>
    } else if (status === 'downloading') {
      return <LoadingIcon className="w-5 h-5 text-gray-700"/>
    } else {
      return null
    }
  }

  const columns: ColumnsType<DataType> = [
    {
      title: thMap.name,
      key: 'modelId',
      render: (_, record) => (
        <div>{`${record.Path}/${record.Name}`}</div>
      )
    },
    {
      title: thMap.dir,
      key: 'directory',
      render: (_, record) => (
        <select
          value={selectedPathMap[record.Id]}
          onChange={(e) => handleSelectedPath(record.Id, e.target.value)}
          className="px-1.5 py-0.5 text-xs rounded-md bg-gray-100
                  text-gray-700 focus:outline-none focus:ring-2 
                  focus:ring-blue-500 hover:!bg-gray-50"
        >
          {modelPaths?.map((path: string) => (
              <option value={path} key={path}>{path}</option>
          ))}
        </select>
      )
    },
    {
      title: thMap.action,
      key: 'action',
      render: (_, record) => (
        <div className="w-full h-full flex justify-center items-center">
          {
            (!!modelDownloadMap[record.Id] && modelDownloadMap[record.Id].status !== 'failed') ? renderDownloadProgress(modelDownloadMap[record.Id]?.status) : <button 
              className="text-gray-900 hover:!text-blue-500 disabled:!text-gray-300 flex justify-center items-center bg-transparent border-none"
              disabled={!!modelDownloadMap[record.Id]}
              onClick={() => handleDownload(record.Id, `${record.Path}/${record.Name}`, record?.model_type || '')}
            >
              <svg viewBox="0 0 1071 1024" className="w-5 h-5" fill="currentColor">
                <path d="M820.376748 284.430361v228.885113a20.509419 20.509419 0 0 0 41.018838 0V249.974538a19.689042 19.689042 0 0 0-2.871319-9.434333v-2.050942a21.739984 21.739984 0 0 0-5.332449-5.332448L423.314402 2.630948a20.509419 20.509419 0 0 0-20.09923 0L10.254709 232.336438a13.946405 13.946405 0 0 0-4.92226 4.92226v2.461131a16.407535 16.407535 0 0 0-5.332449 10.254709v533.244886a8.203767 8.203767 0 0 0 2.46113 2.871319l2.871319 2.871319 392.960462 229.295301a20.09923 20.09923 0 0 0 20.099231 0l196.890419-100.085964a20.919607 20.919607 0 0 0 8.203768-27.892809 20.509419 20.509419 0 0 0-27.89281-8.613956l-164.075349 87.780312v-243.651894l189.917217-102.136905a20.509419 20.509419 0 0 0 11.075086-18.048289V383.695948zM41.018837 287.30168l184.17458 105.8286V615.452379l2.461131 3.281507a11.075086 11.075086 0 0 0 3.281507 2.871319l157.512335 91.882196v252.676038L41.018837 762.710006z m351.941625 210.016448v172.279117l-126.748207-75.88485v-176.381L394.191028 492.395867a22.150172 22.150172 0 0 0-1.230566 3.281507z m20.919608-41.018838l-137.413106-82.037675 146.43725-85.72937L574.263724 369.339355z m0-410.188374l382.295564 205.094187L615.282561 347.189183l-182.944015-98.855399a20.509419 20.509419 0 0 0-20.09923 0L235.448127 351.701255 61.118068 249.974538z m180.072696 549.242233l-159.973466 86.139559v-185.815334-3.691695l160.383654-86.139559zM1066.489773 841.876362a20.509419 20.509419 0 0 0-29.123375 0l-98.035021 95.984079v-229.295301a20.509419 20.509419 0 0 0-41.018837 0v229.295301l-95.98408-95.984079a20.509419 20.509419 0 0 0-29.123375 0 20.509419 20.509419 0 0 0 0 28.713186l131.26028 131.26028a20.919607 20.919607 0 0 0 28.713186 0l131.26028-131.26028a20.509419 20.509419 0 0 0 2.050942-28.713186z">
                </path>
              </svg>
            </button>
          }
        </div>
      )
    },
  ];

  if (!modelPaths) 
    return null

  return <div className="mt-4 w-full h-auto flex-1 min-h-0 overflow-y-auto">
    {
      showTitle && <h3 className="text-xl text-gray-900 font-bold">
        {browserLanguage === 'zh' ? TITLE_ZH : TITLE_EN}
      </h3>
    }
    <Table  
      id="comfyui-copilot-model-download"
      bordered
      loading={loading}
      columns={columns} 
      dataSource={modelSuggests} 
      pagination={showPagination ? undefined : false}
      rowClassName={"text-gray-800"}
      locale={{ emptyText: <TableEmpty /> }}
    />
    <Modal open={!!modalContent && modalContent !== ''} onClose={() => setModalContent(null)}>
      <p>{modalContent}</p>
    </Modal>
  </div>
}

export default ModelOption